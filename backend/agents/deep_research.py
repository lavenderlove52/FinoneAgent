"""DeepResearchAgent with multi-round iterative reasoning."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from backend.agents.base import AgentState, BaseAgent
from backend.agents.reasoning.prompts import (
    BEGIN_SEARCH_RESULT,
    END_SEARCH_RESULT,
    FINAL_ANSWER_PROMPT,
    MAX_SEARCH_LIMIT,
    RELEVANT_EXTRACTION_PROMPT,
)
from backend.agents.reasoning.query_generator import QueryGenerator
from backend.agents.reasoning.thinking_engine import ThinkingEngine
from backend.config import KnowledgeBaseSettings
from backend.retrievers.base import Retriever
from backend.retrievers.markdown import MarkdownRetriever
from backend.retrievers.sqlite import SQLiteRetriever


# 思考进度流前缀，chat.py 用该前缀区分思考事件和最终答案 chunk
THINKING_PREFIX = "\x00THINK:"

SYSTEM_PROMPT = """你是 FinoneAgent DeepResearch 助手。
你只能基于给定的本地知识库检索结果回答；如果证据不足，请说明不足之处。
回答要结构清晰、尽量引用检索来源编号，不要编造未提供的信息。"""


class DeepResearchAgent(BaseAgent):
    """Multi-round deep research agent using iterative retrieval and reasoning."""

    def __init__(
        self,
        *,
        kb_settings: KnowledgeBaseSettings | None = None,
        **kwargs: Any,
    ) -> None:
        self.kb_settings = kb_settings or KnowledgeBaseSettings()
        super().__init__(**kwargs)
        self.thinking_engine = ThinkingEngine(self.llm_client)
        self.query_generator = QueryGenerator(self.llm_client)

    # ------------------------------------------------------------------
    # BaseAgent hooks
    # ------------------------------------------------------------------

    def _setup_tools(self) -> list[Retriever]:
        return [
            MarkdownRetriever(self.kb_settings.md_path),
            SQLiteRetriever(self.kb_settings.sqlite_path),
        ]

    def _generate_node(self, state: AgentState) -> AgentState:
        query = state["query"]
        answer = self.thinking(query)["answer"]
        return {"answer": answer}

    def _build_messages(self, query: str, context: str) -> list[dict[str, str]]:
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "请根据以下本地知识库检索结果回答问题。\n\n"
                    f"问题：{query}\n\n"
                    f"检索结果：\n{context}"
                ),
            },
        ]

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def ask(self, query: str) -> str:
        return self.thinking(query)["answer"]

    def ask_stream(self, query: str) -> Iterator[str]:
        """
        同步流式：实时 yield 每条思考进度（THINKING_PREFIX 前缀），
        检索完成后再流式生成最终答案。
        """
        think = ""
        all_retrieved_info: list[str] = []

        for event in self._research_loop_events(query):
            if event[0] == "progress":
                # 实时转发思考进度，前端可立即收到
                yield f"{THINKING_PREFIX}{event[1]}"
            elif event[0] == "done":
                _, think, all_retrieved_info, _ = event

        if not all_retrieved_info:
            yield f"抱歉，我无法找到关于'{query}'的相关信息。"
        else:
            retrieved_content = "\n\n".join(all_retrieved_info)
            final_msgs = [
                {
                    "role": "system",
                    "content": FINAL_ANSWER_PROMPT.format(
                        query=query,
                        retrieved_content=retrieved_content,
                        thinking_process=think,
                    ),
                },
                {"role": "user", "content": "请基于以上信息给出最终综合回答。"},
            ]
            yield from self.llm_client.stream_chat(final_msgs)

    def ask_with_thinking(self, query: str) -> dict[str, Any]:
        """Return the full thinking result dict."""
        return self.thinking(query)

    # ------------------------------------------------------------------
    # Core multi-round reasoning
    # ------------------------------------------------------------------

    def _research_loop_events(self, query: str) -> Iterator[tuple]:
        """
        核心多轮检索推理生成器。

        每发现进度信息即 yield ("progress", msg)，
        循环结束时 yield ("done", think, all_retrieved_info, logs)。
        调用方可选择实时处理 progress（流式）或统一收集（批量）。
        """
        logs: list[str] = []
        all_retrieved_info: list[str] = []

        self.thinking_engine.initialize_with_query(query)
        initial_sub_queries = self.query_generator.generate_sub_queries(query)

        think = f"我需要回答问题：{query}\n\n为了全面解答，我将从以下方面研究：\n"
        for i, sq in enumerate(initial_sub_queries, 1):
            think += f"{i}. {sq}\n"
        think += "\n让我逐步进行搜索和分析。"
        self.thinking_engine.add_reasoning_step(think)
        yield ("progress", think)

        for iteration in range(MAX_SEARCH_LIMIT + 1):
            if iteration >= MAX_SEARCH_LIMIT:
                logs.append(f"iteration={iteration}: reached MAX_SEARCH_LIMIT")
                break

            self.thinking_engine.update_continue_message()
            queries_to_process: list[str] = []

            if iteration == 0:
                queries_to_process = initial_sub_queries[:2]
            else:
                result = self.thinking_engine.generate_next_query()
                if result["status"] == "answer_ready":
                    logs.append(f"iteration={iteration}: answer_ready")
                    break
                elif result["status"] in ("error", "empty"):
                    hypotheses = self.query_generator.generate_multiple_hypotheses(query)
                    if hypotheses:
                        queries_to_process = hypotheses
                    else:
                        logs.append(f"iteration={iteration}: no hypotheses, stopping")
                        break
                else:
                    content = result.get("content") or ""
                    clean_content = self.thinking_engine.remove_query_tags(content)
                    think += clean_content
                    # 将 LLM 的推理过程也实时展示在思考面板
                    if clean_content.strip():
                        yield ("progress", clean_content)
                    queries_to_process = result["queries"]

            if not queries_to_process:
                if not all_retrieved_info:
                    queries_to_process = [query]
                else:
                    followup = self.query_generator.generate_followup_queries(
                        query, all_retrieved_info
                    )
                    if followup:
                        queries_to_process = followup
                    else:
                        logs.append(f"iteration={iteration}: no followup needed")
                        break

            for search_query in queries_to_process:
                if self.thinking_engine.has_executed_query(search_query):
                    logs.append(f"skip duplicate: {search_query}")
                    continue
                self.thinking_engine.add_executed_query(search_query)

                progress = f"**正在搜索：{search_query}**\n"
                think += f"\n{progress}"
                yield ("progress", progress)
                logs.append(f"search: {search_query}")

                results: list = []
                for retriever in self.retrievers:
                    results.extend(retriever.search(search_query, top_k=3))

                if not results:
                    msg = f"未找到与「{search_query}」相关的信息，尝试其他方向。\n"
                    self.thinking_engine.add_human_message(msg)
                    think += msg
                    yield ("progress", msg)
                    continue

                doc_text = self._format_context(results)
                prev_reasoning = self.thinking_engine.prepare_truncated_reasoning()
                extract_msgs = [
                    {
                        "role": "system",
                        "content": RELEVANT_EXTRACTION_PROMPT.format(
                            prev_reasoning=prev_reasoning,
                            search_query=search_query,
                            document=doc_text,
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f'基于当前的搜索查询"{search_query}"，'
                            "分析每个知识来源并找出有用信息。"
                        ),
                    },
                ]
                yield ("progress", f"正在提取「{search_query}」的相关信息…\n")
                summary = self.llm_client.complete(extract_msgs)

                if (
                    "**Final Information**" in summary
                    and "No helpful information found" not in summary
                ):
                    useful = summary.split("**Final Information**")[1].strip()
                    all_retrieved_info.append(useful)
                    # 完整提取内容，前端思考面板可看到全部分析结果
                    yield ("progress", f"✓ 提取到相关信息：\n\n{useful}\n")
                else:
                    yield ("progress", "此次搜索未提取到有效信息。\n")

                self.thinking_engine.add_reasoning_step(summary)
                self.thinking_engine.add_human_message(
                    f"\n{BEGIN_SEARCH_RESULT}{summary}{END_SEARCH_RESULT}\n"
                )
                think += self.thinking_engine.remove_result_tags(summary)

            if iteration > 0 and all_retrieved_info:
                followup = self.query_generator.generate_followup_queries(
                    query, all_retrieved_info
                )
                if not followup:
                    done_msg = "\n已收集到足够的信息，开始生成最终回答…\n"
                    think += done_msg
                    yield ("progress", done_msg)
                    logs.append(f"iteration={iteration}: sufficient info, stopping")
                    break

        yield ("done", think, all_retrieved_info, logs)

    def thinking(self, query: str) -> dict[str, Any]:
        """
        Execute multi-round deep research reasoning.

        Returns:
            {
                thinking_process: str,
                answer: str,
                retrieved_info: list[str],
                execution_logs: list[str],
            }
        """
        think = ""
        all_retrieved_info: list[str] = []
        logs: list[str] = []

        for event in self._research_loop_events(query):
            if event[0] == "done":
                _, think, all_retrieved_info, logs = event
            # progress 事件在非流式模式下静默忽略

        if not all_retrieved_info:
            answer = f"抱歉，我无法找到关于'{query}'的相关信息。"
        else:
            retrieved_content = "\n\n".join(all_retrieved_info)
            final_msgs = [
                {
                    "role": "system",
                    "content": FINAL_ANSWER_PROMPT.format(
                        query=query,
                        retrieved_content=retrieved_content,
                        thinking_process=think,
                    ),
                },
                {"role": "user", "content": "请基于以上信息给出最终综合回答。"},
            ]
            answer = self.llm_client.complete(final_msgs)

        return {
            "thinking_process": think,
            "answer": answer,
            "retrieved_info": all_retrieved_info,
            "execution_logs": logs,
        }
