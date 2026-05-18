from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from backend.llm_client import LLMClient
from backend.retrievers.base import RetrievalResult, Retriever
from backend.retrievers.keyword import extract_terms


class AgentState(TypedDict, total=False):
    query: str
    keywords: list[str]
    results: list[RetrievalResult]
    context: str
    answer: str


class BaseAgent(ABC):
    """Lightweight LangGraph-backed base class for FinoneAgent agents."""

    def __init__(
        self,
        *,
        llm_client: LLMClient | None = None,
        top_k: int = 5,
    ) -> None:
        self.llm_client = llm_client or LLMClient()
        self.top_k = top_k
        self.retrievers = self._setup_tools()
        self.graph = self._build_graph()

    @abstractmethod
    def _setup_tools(self) -> list[Retriever]:
        """Register retrievers or tools for the concrete agent."""

    def _build_graph(self) -> Any:
        graph = StateGraph(AgentState)
        graph.add_node("agent", self._agent_node)
        graph.add_node("retrieve", self._retrieve_node)
        graph.add_node("generate", self._generate_node)
        graph.set_entry_point("agent")
        graph.add_edge("agent", "retrieve")
        self._add_retrieval_edges(graph)
        return graph.compile()

    def _add_retrieval_edges(self, graph: StateGraph) -> None:
        graph.add_edge("retrieve", "generate")
        graph.add_edge("generate", END)

    def _extract_keywords(self, query: str) -> list[str]:
        return extract_terms(query)

    def _agent_node(self, state: AgentState) -> AgentState:
        query = state["query"]
        return {"keywords": self._extract_keywords(query)}

    def _retrieve_node(self, state: AgentState) -> AgentState:
        query = state["query"]
        results: list[RetrievalResult] = []
        per_retriever_top_k = max(1, self.top_k)
        for retriever in self.retrievers:
            results.extend(retriever.search(query, top_k=per_retriever_top_k))
        results = sorted(results, key=lambda item: item.score, reverse=True)[
            : self.top_k
        ]
        return {"results": results, "context": self._format_context(results)}

    def _format_context(self, results: list[RetrievalResult]) -> str:
        if not results:
            return "未检索到相关本地知识。"
        blocks = []
        for index, item in enumerate(results, start=1):
            blocks.append(
                "\n".join(
                    [
                        f"[{index}] {item.title}",
                        f"source_type: {item.source_type}",
                        f"source_id: {item.source_id}",
                        f"score: {item.score:.2f}",
                        item.content,
                    ]
                )
            )
        return "\n\n".join(blocks)

    @abstractmethod
    def _generate_node(self, state: AgentState) -> AgentState:
        """Generate a final answer for non-streaming graph execution."""

    @abstractmethod
    def _build_messages(self, query: str, context: str) -> list[dict[str, str]]:
        """Build messages for the unified LLM client."""

    def ask(self, query: str) -> str:
        state = self.graph.invoke({"query": query})
        return state.get("answer", "")

    def ask_stream(self, query: str) -> Iterator[str]:
        state: AgentState = {"query": query}
        state.update(self._agent_node(state))
        state.update(self._retrieve_node(state))
        messages = self._build_messages(query, state.get("context", ""))
        yield from self.llm_client.stream_chat(messages)

    def retrieve(self, query: str) -> list[RetrievalResult]:
        state: AgentState = {"query": query}
        state.update(self._retrieve_node(state))
        return state.get("results", [])

    def close(self) -> None:
        """Hook for future resources; MVP retrievers do not keep open handles."""

