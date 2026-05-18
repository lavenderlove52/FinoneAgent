"""DeepResearchAgent with multi-round iterative reasoning."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from backend.agents.base import AgentState, BaseAgent
from backend.agents.reasoning.answer_validator import AnswerValidator
from backend.agents.reasoning.prompts import (
    BEGIN_SEARCH_RESULT,
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
        self.answer_validator = AnswerValidator()

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
        Synchronous streaming: yield progress during retrieval then stream
        the final answer token-by-token.
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

        for iteration in range(MAX_SEARCH_LIMIT):
            if iteration >= MAX_SEARCH_LIMIT - 1:
                break

            self.thinking_engine.update_continue_message()

            if iteration == 0:
                queries_to_process = initial_sub_queries[:2]
            else:
                result = self.thinking_engine.generate_next_query()
                if result["status"] == "answer_ready":
                    break
                elif result["status"] in ("error", "empty"):
                    hypotheses = self.query_generator.generate_multiple_hypotheses(query)
                    if hypotheses:
                        queries_to_process = hypotheses
                    else:
                        break
                else:
                    content = result.get("content") or ""
                    think += self.thinking_engine.remove_query_tags(content)
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
                        break

            for search_query in queries_to_process:
                if self.thinking_engine.has_executed_query(search_query):
                    continue
                self.thinking_engine.add_executed_query(search_query)

                yield f"**正在搜索：{search_query}**\n"

                results = []
                for retriever in self.retrievers:
                    results.extend(retriever.search(search_query, top_k=3))

                if not results:
                    no_result_msg = f"\n没有找到与'{search_query}'相关的信息。\n"
                    self.thinking_engine.add_human_message(no_result_msg)
                    think += no_result_msg
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
                summary = self.llm_client.complete(extract_msgs)

                if (
                    "**Final Information**" in summary
                    and "No helpful information found" not in summary
                ):
                    useful = summary.split("**Final Information**")[1].strip()
                    all_retrieved_info.append(useful)

                self.thinking_engine.add_reasoning_step(summary)
                self.thinking_engine.add_human_message(
                    f"\n{BEGIN_SEARCH_RESULT}{summary}{BEGIN_SEARCH_RESULT}\n"
                )
                think += self.thinking_engine.remove_result_tags(summary)

            if iteration > 0 and all_retrieved_info:
                followup = self.query_generator.generate_followup_queries(
                    query, all_retrieved_info
                )
                if not followup:
                    think += "\n已收集到足够的信息，可以开始整合分析了。"
                    break

        # Stream final answer
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
        logs: list[str] = []
        all_retrieved_info: list[str] = []

        self.thinking_engine.initialize_with_query(query)
        initial_sub_queries = self.query_generator.generate_sub_queries(query)

        think = f"我需要回答问题：{query}\n\n为了全面解答，我将从以下方面研究：\n"
        for i, sq in enumerate(initial_sub_queries, 1):
            think += f"{i}. {sq}\n"
        think += "\n让我逐步进行搜索和分析。"
        self.thinking_engine.add_reasoning_step(think)

        for iteration in range(MAX_SEARCH_LIMIT):
            if iteration >= MAX_SEARCH_LIMIT - 1:
                logs.append(f"iteration={iteration}: reached MAX_SEARCH_LIMIT")
                break

            self.thinking_engine.update_continue_message()

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
                        logs.append(f"iteration={iteration}: error/empty, no hypotheses")
                        break
                else:
                    content = result.get("content") or ""
                    think += self.thinking_engine.remove_query_tags(content)
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
                    logs.append(f"skip duplicate query: {search_query}")
                    continue
                self.thinking_engine.add_executed_query(search_query)
                think += f"\n\n> 搜索：{search_query}\n\n"
                logs.append(f"search: {search_query}")

                results = []
                for retriever in self.retrievers:
                    results.extend(retriever.search(search_query, top_k=3))

                if not results:
                    no_result_msg = f"\n没有找到与'{search_query}'相关的信息。\n"
                    self.thinking_engine.add_human_message(no_result_msg)
                    think += no_result_msg
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
                summary = self.llm_client.complete(extract_msgs)

                if (
                    "**Final Information**" in summary
                    and "No helpful information found" not in summary
                ):
                    useful = summary.split("**Final Information**")[1].strip()
                    all_retrieved_info.append(useful)

                self.thinking_engine.add_reasoning_step(summary)
                self.thinking_engine.add_human_message(
                    f"\n{BEGIN_SEARCH_RESULT}{summary}{BEGIN_SEARCH_RESULT}\n"
                )
                think += self.thinking_engine.remove_result_tags(summary)

            if iteration > 0 and all_retrieved_info:
                followup = self.query_generator.generate_followup_queries(
                    query, all_retrieved_info
                )
                if not followup:
                    think += "\n已收集到足够的信息，可以开始整合分析了。"
                    logs.append(f"iteration={iteration}: sufficient info, stopping")
                    break

        # Generate final answer
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
