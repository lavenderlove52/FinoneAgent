# FinoneAgent 第一阶段 MVP

FinoneAgent 第一阶段 MVP 的目标是构建一个最小可运行的 DeepResearchAgent。后端使用 LangGraph 编排 agent、retrieve、generate 三个节点，通过统一 LLMClient 调用 OpenAI 兼容的大模型网关。

## 本地知识库

MVP 只支持 Markdown 和 SQLite 两类本地知识库。Markdown 知识库位于 backend/knowledge_base/md，只读取 .md 文件，并按标题与段落切分后使用关键词评分检索。

## 外部组件范围

Redis、Neo4j、GraphRAG、社区搜索和知识图谱探索在第一阶段只保留接口占位。MVP 不连接这些外部系统，也不安装它们的依赖。

