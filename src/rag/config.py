"""
RAG 模块配置

从环境变量加载 Milvus 和嵌入模型配置
"""
import os
from dataclasses import dataclass, field
from typing import Optional
from functools import lru_cache


@dataclass
class RAGConfig:
    """
    RAG 配置类
    
    属性:
        milvus_host: Milvus 服务器地址
        milvus_port: Milvus 服务器端口
        milvus_database: Milvus 数据库名称
        chinese_collection: 中文文档集合名称
        english_collection: 英文文档集合名称
        embedding_model: 嵌入模型名称
        embedding_dimension: 向量维度
        rerank_model: 重排序模型名称
        top_k_retrieve: 初始检索数量
        top_k_rerank: 重排序后返回数量
        dashscope_api_key: DashScope API 密钥
    """
    # Milvus 配置
    milvus_host: str = field(default_factory=lambda: os.getenv("MILVUS_HOST", "localhost"))
    milvus_port: int = field(default_factory=lambda: int(os.getenv("MILVUS_PORT", "19530")))
    milvus_database: str = field(default_factory=lambda: os.getenv("MILVUS_DATABASE", "materials_rag"))
    milvus_username: Optional[str] = field(default_factory=lambda: os.getenv("MILVUS_USERNAME"))
    milvus_password: Optional[str] = field(default_factory=lambda: os.getenv("MILVUS_PASSWORD"))
    
    # 集合配置
    chinese_collection: str = field(
        default_factory=lambda: os.getenv("MILVUS_CHINESE_COLLECTION", "materials_docs_chinese_hybrid")
    )
    english_collection: str = field(
        default_factory=lambda: os.getenv("MILVUS_ENGLISH_COLLECTION", "materials_docs_english_hybrid")
    )
    
    # 嵌入模型配置
    embedding_model: str = field(
        default_factory=lambda: os.getenv("EMBEDDING_MODEL", "text-embedding-v3")
    )
    embedding_dimension: int = field(
        default_factory=lambda: int(os.getenv("EMBEDDING_DIMENSION", "1024"))
    )
    
    # 重排序配置
    rerank_model: str = field(
        default_factory=lambda: os.getenv("RERANK_MODEL", "gte-rerank-v2")
    )
    
    # 检索配置（中英文分开）
    top_k_cn: int = field(
        default_factory=lambda: int(os.getenv("RAG_TOP_K_CN", "10"))
    )
    top_k_en: int = field(
        default_factory=lambda: int(os.getenv("RAG_TOP_K_EN", "10"))
    )
    
    # API 配置
    dashscope_api_key: str = field(
        default_factory=lambda: os.getenv("DASHSCOPE_API_KEY", "")
    )
    
    def __post_init__(self):
        """验证必需的配置"""
        if not self.dashscope_api_key:
            raise ValueError("DASHSCOPE_API_KEY 环境变量未设置")


@lru_cache()
def get_rag_config() -> RAGConfig:
    """
    获取 RAG 配置单例
    
    返回:
        RAGConfig: RAG 配置实例
    """
    return RAGConfig()
