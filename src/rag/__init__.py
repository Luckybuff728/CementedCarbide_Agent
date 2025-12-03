"""
RAG 检索增强生成模块

提供基于 Milvus 向量数据库的知识检索功能：
- 向量嵌入：使用 DashScope text-embedding-v3
- 向量存储：Milvus 向量数据库
- 混合检索：语义检索 + BM25 全文检索
- 重排序：使用 DashScope gte-rerank 模型
"""

from .config import RAGConfig, get_rag_config
from .embedding import EmbeddingService, get_embedding_service
from .milvus_client import MilvusClient, get_milvus_client
from .retriever import RAGRetriever, get_rag_retriever

__all__ = [
    # 配置
    "RAGConfig",
    "get_rag_config",
    
    # 嵌入服务
    "EmbeddingService",
    "get_embedding_service",
    
    # Milvus 客户端
    "MilvusClient",
    "get_milvus_client",
    
    # 检索器
    "RAGRetriever",
    "get_rag_retriever",
]
