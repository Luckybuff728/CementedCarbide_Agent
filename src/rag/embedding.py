"""
嵌入模型服务

使用 DashScope text-embedding 模型生成文本向量
"""
import dashscope
from dashscope import TextEmbedding
from typing import List, Union, Optional
from functools import lru_cache
from loguru import logger

from .config import RAGConfig, get_rag_config


class EmbeddingService:
    """
    嵌入模型服务
    
    使用阿里云 DashScope 的 text-embedding 模型
    支持中英文双语文本嵌入
    """
    
    def __init__(self, config: Optional[RAGConfig] = None):
        """
        初始化嵌入服务
        
        参数:
            config: RAG 配置，如不提供则使用默认配置
        """
        self.config = config or get_rag_config()
        dashscope.api_key = self.config.dashscope_api_key
        self.model = self.config.embedding_model
        self.dimension = self.config.embedding_dimension
        logger.info(f"嵌入服务初始化完成，模型: {self.model}, 维度: {self.dimension}")
    
    def embed_text(self, text: str) -> List[float]:
        """
        对单个文本生成向量
        
        参数:
            text: 输入文本
            
        返回:
            List[float]: 向量列表
        """
        try:
            response = TextEmbedding.call(
                model=self.model,
                input=text,
                dimension=self.dimension
            )
            
            if response.status_code == 200:
                return response.output["embeddings"][0]["embedding"]
            else:
                logger.error(f"嵌入失败: {response.code} - {response.message}")
                raise Exception(f"嵌入失败: {response.message}")
                
        except Exception as e:
            logger.error(f"嵌入服务错误: {e}")
            raise
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        批量生成文本向量
        
        参数:
            texts: 文本列表
            
        返回:
            List[List[float]]: 向量列表的列表
        """
        if not texts:
            return []
        
        try:
            # DashScope 支持批量嵌入，最大 25 条
            batch_size = 25
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                response = TextEmbedding.call(
                    model=self.model,
                    input=batch,
                    dimension=self.dimension
                )
                
                if response.status_code == 200:
                    batch_embeddings = [
                        item["embedding"] 
                        for item in response.output["embeddings"]
                    ]
                    all_embeddings.extend(batch_embeddings)
                else:
                    logger.error(f"批量嵌入失败: {response.code} - {response.message}")
                    raise Exception(f"批量嵌入失败: {response.message}")
            
            return all_embeddings
            
        except Exception as e:
            logger.error(f"批量嵌入服务错误: {e}")
            raise
    
    def embed_query(self, query: str) -> List[float]:
        """
        对查询文本生成向量（别名方法，与 LangChain 接口兼容）
        
        参数:
            query: 查询文本
            
        返回:
            List[float]: 查询向量
        """
        return self.embed_text(query)


@lru_cache()
def get_embedding_service() -> EmbeddingService:
    """
    获取嵌入服务单例
    
    返回:
        EmbeddingService: 嵌入服务实例
    """
    return EmbeddingService()
