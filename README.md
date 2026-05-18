# FinoneAgent

第一阶段 MVP 实现一个最小可运行的 DeepResearchAgent 后端。前端目录仅占位。

## 目录

- `backend/agents/`: 轻量 `BaseAgent` 与 `DeepResearchAgent`。
- `backend/llm_client.py`: 统一大模型调用入口，封装 `OpenAI(base_url="https://aigw.fosunwealth.com/v1", api_key=...)`。
- `backend/retrievers/`: 统一 `Retriever` 接口、`RetrievalResult` schema、Markdown/SQLite 检索器和外部组件 stub。
- `backend/knowledge_base/md/`: Markdown 示例知识库，只支持 `.md`。
- `backend/knowledge_base/sqlite/knowledge.db`: SQLite 示例知识库。
- `frontend/`: 第一阶段占位。

## 环境变量

复制 `.env.example` 或在当前 shell 中设置：

```powershell
$env:AIGW_API_KEY="your-api-key"
$env:AIGW_BASE_URL="https://aigw.fosunwealth.com/v1"
$env:AIGW_MODEL="claude-opus-4.6"
```

`AIGW_API_KEY` 可回退到 `OPENAI_API_KEY`。没有 API key 时仍可运行本地检索验证，但不能调用远程模型。

## 安装依赖

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 初始化 SQLite 示例库

```powershell
.\.venv\Scripts\python.exe -m backend.scripts.init_sqlite_kb
```

## 运行

仅检索本地知识库：

```powershell
.\.venv\Scripts\python.exe -m backend.cli "FinoneAgent MVP 支持哪些知识库" --retrieve-only
```

流式回答：

```powershell
.\.venv\Scripts\python.exe -m backend.cli "FinoneAgent MVP 支持哪些知识库"
```

也可以在代码中调用：

```python
from backend.agents import DeepResearchAgent

agent = DeepResearchAgent()
for chunk in agent.ask_stream("FinoneAgent MVP 支持哪些知识库"):
    print(chunk, end="", flush=True)
```

## MVP 范围

已实现：

- LangGraph 最小节点：`agent -> retrieve -> generate`。
- 统一 `LLMClient`，所有 LLM 调用都经过该封装。
- Markdown 按标题/段落分块，关键词评分检索。
- SQLite `documents(id, title, content, source)` 表，参数化 `LIKE` 检索。
- `ask_stream(query)` 流式接口。

仅占位：

- Redis、Neo4j、GraphRAG、社区搜索、知识图谱探索。
- 前端页面。
- PDF/DOCX、向量检索、FTS5、多轮复杂推理、缓存与答案校验。

