"""
RAG 检索器

实现双语检索 + 重排序 + 答案生成的完整 RAG 流程
"""
import dashscope
from dashscope import TextReRank, Generation
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from functools import lru_cache
from loguru import logger

from .config import RAGConfig, get_rag_config
from .milvus_client import MilvusClient, SearchResult, get_milvus_client


@dataclass
class RetrievalResult:
    """
    RAG 检索结果
    
    属性:
        query: 原始查询
        documents: 检索到的文档列表
        answer: 生成的答案（如果有）
        sources: 来源引用
    """
    query: str
    documents: List[SearchResult] = field(default_factory=list)
    answer: str = ""
    sources: List[str] = field(default_factory=list)


class RAGRetriever:
    """
    RAG 检索器
    
    支持功能：
    1. 双语并行检索（中文 + 英文集合）
    2. 重排序优化
    3. 基于检索结果的答案生成
    """
    
    def __init__(
        self,
        config: Optional[RAGConfig] = None,
        milvus_client: Optional[MilvusClient] = None
    ):
        """
        初始化 RAG 检索器
        
        参数:
            config: RAG 配置
            milvus_client: Milvus 客户端
        """
        self.config = config or get_rag_config()
        self.milvus_client = milvus_client or get_milvus_client()
        dashscope.api_key = self.config.dashscope_api_key
        
        logger.info("RAG 检索器初始化完成")
    
    def _rerank(
        self,
        query: str,
        documents: List[SearchResult],
        top_k: int
    ) -> List[SearchResult]:
        """
        对检索结果进行重排序
        
        参数:
            query: 查询文本
            documents: 检索结果列表
            top_k: 返回数量
            
        返回:
            List[SearchResult]: 重排序后的结果
        """
        if not documents:
            return []
        
        try:
            # 准备文档内容
            doc_texts = [doc.content for doc in documents]
            
            # 调用重排序 API
            response = TextReRank.call(
                model=self.config.rerank_model,
                query=query,
                documents=doc_texts,
                top_n=min(top_k, len(documents))
            )
            
            if response.status_code == 200:
                # 根据重排序结果重新排列
                reranked = []
                for item in response.output["results"]:
                    idx = item["index"]
                    doc = documents[idx]
                    # 更新分数为重排序分数
                    doc.score = item["relevance_score"]
                    reranked.append(doc)
                
                logger.debug(f"重排序完成，返回 {len(reranked)} 条结果")
                return reranked
            else:
                logger.warning(f"重排序失败: {response.message}，使用原始排序")
                return documents[:top_k]
                
        except Exception as e:
            logger.warning(f"重排序异常: {e}，使用原始排序")
            return documents[:top_k]
    
    def retrieve(
        self,
        query: str,
        use_chinese: bool = True,
        use_english: bool = True,
        use_rerank: bool = True,
        top_k: Optional[int] = None
    ) -> List[SearchResult]:
        """
        执行检索
        
        参数:
            query: 查询文本
            use_chinese: 是否检索中文集合
            use_english: 是否检索英文集合
            use_rerank: 是否使用重排序
            top_k: 返回数量
            
        返回:
            List[SearchResult]: 检索结果列表
        """
        top_k = top_k or self.config.top_k_rerank
        retrieve_k = self.config.top_k_retrieve
        
        all_results: List[SearchResult] = []
        
        # 中文检索
        if use_chinese:
            try:
                cn_results = self.milvus_client.hybrid_search(
                    query=query,
                    collection_name=self.config.chinese_collection,
                    top_k=retrieve_k
                )
                all_results.extend(cn_results)
                logger.info(f"中文检索返回 {len(cn_results)} 条结果")
            except Exception as e:
                logger.warning(f"中文检索失败: {e}")
        
        # 英文检索
        if use_english:
            try:
                en_results = self.milvus_client.hybrid_search(
                    query=query,
                    collection_name=self.config.english_collection,
                    top_k=retrieve_k
                )
                all_results.extend(en_results)
                logger.info(f"英文检索返回 {len(en_results)} 条结果")
            except Exception as e:
                logger.warning(f"英文检索失败: {e}")
        
        if not all_results:
            logger.warning("未检索到任何结果")
            return []
        
        # 重排序
        if use_rerank and len(all_results) > top_k:
            all_results = self._rerank(query, all_results, top_k)
        else:
            # 按分数排序并截取
            all_results.sort(key=lambda x: x.score, reverse=True)
            all_results = all_results[:top_k]
        
        return all_results
    
    def generate_answer(
        self,
        query: str,
        documents: List[SearchResult],
        model: str = "qwen-max-latest"
    ) -> str:
        """
        基于检索结果生成答案
        
        参数:
            query: 查询问题
            documents: 检索到的文档
            model: 生成模型名称
            
        返回:
            str: 生成的答案
        """
        if not documents:
            return "抱歉，未能找到相关文献信息来回答您的问题。"
        
        # 构建上下文
        context_parts = []
        for i, doc in enumerate(documents, 1):
            title = doc.metadata.get("title", "未知来源")
            context_parts.append(f"[文献{i}] {title}\n{doc.content}")
        
        context = "\n\n---\n\n".join(context_parts)
        
        # 构建提示词
        prompt = f"""你是一位材料科学领域的专家。请基于以下检索到的文献内容，回答用户的问题。

## 检索到的文献内容

{context}

## 用户问题

{query}

## 回答要求

1. 请基于上述文献内容进行回答，确保答案有据可依
2. 如果文献中没有相关信息，请明确说明
3. 适当引用文献编号（如[文献1]）以支持你的回答
4. 使用专业但易懂的语言
5. 如果涉及具体数据或参数，请准确引用

请开始回答："""

        try:
            response = Generation.call(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                result_format="message"
            )
            
            if response.status_code == 200:
                return response.output.choices[0].message.content
            else:
                logger.error(f"答案生成失败: {response.message}")
                return f"答案生成失败: {response.message}"
                
        except Exception as e:
            logger.error(f"答案生成异常: {e}")
            return f"答案生成过程中发生错误: {str(e)}"
    
    def query(
        self,
        question: str,
        use_chinese: bool = True,
        use_english: bool = True,
        generate_answer: bool = True,
        top_k: Optional[int] = None
    ) -> RetrievalResult:
        """
        完整的 RAG 查询流程
        
        参数:
            question: 用户问题
            use_chinese: 是否检索中文集合
            use_english: 是否检索英文集合
            generate_answer: 是否生成答案
            top_k: 返回文档数量
            
        返回:
            RetrievalResult: 检索结果
        """
        logger.info(f"开始 RAG 查询: {question[:50]}...")
        
        # 检索
        documents = self.retrieve(
            query=question,
            use_chinese=use_chinese,
            use_english=use_english,
            top_k=top_k
        )
        
        result = RetrievalResult(
            query=question,
            documents=documents,
            sources=[
                doc.metadata.get("title", "未知来源") 
                for doc in documents
            ]
        )
        
        # 生成答案
        if generate_answer and documents:
            result.answer = self.generate_answer(question, documents)
        
        logger.info(f"RAG 查询完成，检索到 {len(documents)} 篇文献")
        return result
    
    def simple_query(self, question: str) -> str:
        """
        简单查询接口，直接返回答案文本
        
        参数:
            question: 用户问题
            
        返回:
            str: 答案文本
        """
        result = self.query(question)
        
        if result.answer:
            # 添加来源引用
            if result.sources:
                sources_text = "\n\n---\n📚 **参考文献**:\n" + "\n".join(
                    f"- {src}" for src in set(result.sources)
                )
                return result.answer + sources_text
            return result.answer
        else:
            return "抱歉，未能找到相关信息来回答您的问题。"


# 全局检索器实例
_rag_retriever: Optional[RAGRetriever] = None


def get_rag_retriever() -> RAGRetriever:
    """
    获取 RAG 检索器单例
    
    返回:
        RAGRetriever: RAG 检索器实例
    """
    global _rag_retriever
    if _rag_retriever is None:
        _rag_retriever = RAGRetriever()
    return _rag_retriever
