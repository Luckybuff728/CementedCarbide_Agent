"""
Milvus 向量数据库客户端

提供与 Milvus 数据库的连接和检索功能
"""
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from functools import lru_cache
from loguru import logger

try:
    from pymilvus import (
        connections,
        Collection,
        utility,
        MilvusException
    )
    MILVUS_AVAILABLE = True
except ImportError:
    MILVUS_AVAILABLE = False
    logger.warning("pymilvus 未安装，Milvus 功能不可用")

from .config import RAGConfig, get_rag_config
from .embedding import EmbeddingService, get_embedding_service


@dataclass
class SearchResult:
    """
    检索结果
    
    属性:
        content: 文档内容
        score: 相关性分数
        metadata: 元数据（标题、来源等）
        chunk_id: 文档块ID
    """
    content: str
    score: float
    metadata: Dict[str, Any]
    chunk_id: str
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "content": self.content,
            "score": self.score,
            "metadata": self.metadata,
            "chunk_id": self.chunk_id
        }


class MilvusClient:
    """
    Milvus 向量数据库客户端
    
    提供连接管理、向量检索等功能
    """
    
    def __init__(
        self, 
        config: Optional[RAGConfig] = None,
        embedding_service: Optional[EmbeddingService] = None
    ):
        """
        初始化 Milvus 客户端
        
        参数:
            config: RAG 配置
            embedding_service: 嵌入服务
        """
        if not MILVUS_AVAILABLE:
            raise ImportError("pymilvus 未安装，请运行: pip install pymilvus")
        
        self.config = config or get_rag_config()
        self.embedding_service = embedding_service or get_embedding_service()
        self._connected = False
        self._collections: Dict[str, Collection] = {}
        
        # 连接到 Milvus
        self._connect()
    
    def _connect(self, max_retries: int = 3, retry_delay: float = 2.0):
        """
        建立 Milvus 连接（带重试机制）
        
        参数:
            max_retries: 最大重试次数
            retry_delay: 重试间隔（秒）
        """
        import time
        
        # 构建连接参数
        conn_params = {
            "alias": "default",
            "host": self.config.milvus_host,
            "port": self.config.milvus_port,
            "db_name": self.config.milvus_database
        }
        
        # 添加认证信息（如果有）
        if self.config.milvus_username and self.config.milvus_password:
            conn_params["user"] = self.config.milvus_username
            conn_params["password"] = self.config.milvus_password
        
        last_error = None
        for attempt in range(max_retries):
            try:
                # 检查是否已有连接，先断开
                try:
                    connections.disconnect("default")
                except Exception:
                    pass
                
                connections.connect(**conn_params)
                self._connected = True
                logger.info(
                    f"Milvus 连接成功: {self.config.milvus_host}:{self.config.milvus_port}"
                    f"/{self.config.milvus_database}"
                )
                return  # 连接成功，退出
                
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    logger.warning(f"Milvus 连接失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"Milvus 连接失败 (已重试 {max_retries} 次): {e}")
        
        raise last_error
    
    def _get_collection(self, collection_name: str) -> Collection:
        """
        获取集合对象
        
        参数:
            collection_name: 集合名称
            
        返回:
            Collection: Milvus 集合对象
        """
        if collection_name not in self._collections:
            if not utility.has_collection(collection_name):
                raise ValueError(f"集合 '{collection_name}' 不存在")
            
            collection = Collection(collection_name)
            collection.load()
            self._collections[collection_name] = collection
            logger.info(f"加载集合: {collection_name}")
        
        return self._collections[collection_name]
    
    def search(
        self,
        query: str,
        collection_name: str,
        top_k: int = 10,
        output_fields: Optional[List[str]] = None
    ) -> List[SearchResult]:
        """
        向量相似度检索
        
        参数:
            query: 查询文本
            collection_name: 集合名称
            top_k: 返回结果数量
            output_fields: 需要返回的字段列表
            
        返回:
            List[SearchResult]: 检索结果列表
        """
        try:
            # 生成查询向量
            query_vector = self.embedding_service.embed_query(query)
            
            # 获取集合
            collection = self._get_collection(collection_name)
            
            # 默认输出字段（匹配集合 schema）
            if output_fields is None:
                output_fields = [
                    "content", "title", "doc_type", "page_num", 
                    "metadata", "materials", "processes"
                ]
            
            # 执行检索
            results = collection.search(
                data=[query_vector],
                anns_field="dense_vector",
                param={"metric_type": "IP", "params": {"nprobe": 16}},
                limit=top_k,
                output_fields=output_fields
            )
            
            # 转换结果
            search_results = []
            for hits in results:
                for hit in hits:
                    entity = hit.entity
                    result = SearchResult(
                        content=entity.get("content", ""),
                        score=hit.score,
                        metadata={
                            "title": entity.get("title", ""),
                            "doc_type": entity.get("doc_type", ""),
                            "page_num": entity.get("page_num", ""),
                            "metadata": entity.get("metadata", ""),  # JSON 字符串
                            "materials": entity.get("materials", ""),
                            "processes": entity.get("processes", ""),
                        },
                        chunk_id=str(hit.id)
                    )
                    search_results.append(result)
            
            logger.info(f"检索完成: {collection_name}, 返回 {len(search_results)} 条结果")
            return search_results
            
        except Exception as e:
            logger.error(f"检索失败: {e}")
            raise
    
    def hybrid_search(
        self,
        query: str,
        collection_name: str,
        top_k: int = 10,
        semantic_weight: float = 0.7,
        bm25_weight: float = 0.3,
        output_fields: Optional[List[str]] = None
    ) -> List[SearchResult]:
        """
        混合检索（语义 + BM25）
        
        参数:
            query: 查询文本
            collection_name: 集合名称
            top_k: 返回结果数量
            semantic_weight: 语义检索权重
            bm25_weight: BM25 检索权重
            output_fields: 需要返回的字段列表
            
        返回:
            List[SearchResult]: 检索结果列表
        """
        try:
            from pymilvus import AnnSearchRequest, RRFRanker
            
            # 生成查询向量
            query_vector = self.embedding_service.embed_query(query)
            
            # 获取集合
            collection = self._get_collection(collection_name)
            
            # 默认输出字段（匹配集合 schema）
            if output_fields is None:
                output_fields = [
                    "content", "title", "doc_type", "page_num", 
                    "metadata", "materials", "processes"
                ]
            
            # 语义检索请求
            semantic_req = AnnSearchRequest(
                data=[query_vector],
                anns_field="dense_vector",
                param={"metric_type": "IP", "params": {"nprobe": 16}},
                limit=top_k * 2
            )
            
            # BM25 检索请求（如果集合支持）
            search_requests = [semantic_req]
            
            # 检查是否有 BM25 索引
            try:
                bm25_req = AnnSearchRequest(
                    data=[query],
                    anns_field="sparse_vector",
                    param={"metric_type": "BM25"},
                    limit=top_k * 2
                )
                search_requests.append(bm25_req)
            except Exception:
                # 如果没有 BM25 索引，只使用语义检索
                logger.debug(f"集合 {collection_name} 不支持 BM25，使用纯语义检索")
            
            # 执行混合检索
            if len(search_requests) > 1:
                results = collection.hybrid_search(
                    reqs=search_requests,
                    rerank=RRFRanker(k=60),
                    limit=top_k,
                    output_fields=output_fields
                )
            else:
                # 降级为普通语义检索
                return self.search(query, collection_name, top_k, output_fields)
            
            # 转换结果
            search_results = []
            for hits in results:
                for hit in hits:
                    entity = hit.entity
                    result = SearchResult(
                        content=entity.get("content", ""),
                        score=hit.score,
                        metadata={
                            "title": entity.get("title", ""),
                            "doc_type": entity.get("doc_type", ""),
                            "page_num": entity.get("page_num", ""),
                            "metadata": entity.get("metadata", ""),
                            "materials": entity.get("materials", ""),
                            "processes": entity.get("processes", ""),
                        },
                        chunk_id=str(hit.id)
                    )
                    search_results.append(result)
            
            logger.info(f"混合检索完成: {collection_name}, 返回 {len(search_results)} 条结果")
            return search_results
            
        except Exception as e:
            logger.warning(f"混合检索失败，降级为语义检索: {e}")
            return self.search(query, collection_name, top_k, output_fields)
    
    def close(self):
        """关闭连接"""
        if self._connected:
            connections.disconnect("default")
            self._connected = False
            logger.info("Milvus 连接已关闭")


# 全局客户端实例
_milvus_client: Optional[MilvusClient] = None


def get_milvus_client() -> MilvusClient:
    """
    获取 Milvus 客户端单例
    
    返回:
        MilvusClient: Milvus 客户端实例
    """
    global _milvus_client
    if _milvus_client is None:
        _milvus_client = MilvusClient()
    return _milvus_client
