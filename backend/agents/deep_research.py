from __future__ import annotations

from backend.agents.base import AgentState, BaseAgent
from backend.config import KnowledgeBaseSettings
from backend.retrievers.base import Retriever
from backend.retrievers.markdown import MarkdownRetriever
from backend.retrievers.sqlite import SQLiteRetriever


SYSTEM_PROMPT = """你是 FinoneAgent 第一阶段 DeepResearch 助手。
你只能基于给定的本地知识库检索结果回答；如果证据不足，请说明不足之处。
回答要结构清晰、尽量引用检索来源编号，不要编造未提供的信息。"""


class DeepResearchAgent(BaseAgent):
    """First MVP implementation using Markdown and SQLite local retrieval."""

    def __init__(
        self,
        *,
        kb_settings: KnowledgeBaseSettings | None = None,
        **kwargs: object,
    ) -> None:
        self.kb_settings = kb_settings or KnowledgeBaseSettings()
        super().__init__(**kwargs)

    def _setup_tools(self) -> list[Retriever]:
        return [
            MarkdownRetriever(self.kb_settings.md_path),
            SQLiteRetriever(self.kb_settings.sqlite_path),
        ]

    def _generate_node(self, state: AgentState) -> AgentState:
        query = state["query"]
        context = state.get("context", "")
        answer = self.llm_client.complete(self._build_messages(query, context))
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

