"""
RAG 检索工具 (优化版)
- 查询增强：将用户问题增强为中英文查询
- 分别检索中英文集合，整合结果
- 返回结构化文献内容供 Agent 分析
"""
from typing import Optional, List, Tuple
import os

from langchain_core.tools import tool
from loguru import logger

# 导入内部 RAG 模块
try:
    from src.rag import MilvusClient, get_milvus_client, get_rag_config
    from src.rag.milvus_client import SearchResult
    RAG_AVAILABLE = True
except ImportError as e:
    logger.warning(f"RAG 模块导入失败: {e}")
    RAG_AVAILABLE = False
    MilvusClient = None

# 全局客户端实例
_client: Optional[MilvusClient] = None


def _enhance_query(question: str) -> Tuple[str, str]:
    """
    查询增强：将用户问题转换为优化的中英文查询
    
    参数:
        question: 用户原始问题
        
    返回:
        Tuple[str, str]: (中文增强查询, 英文增强查询)
    """
    try:
        import openai
        
        client = openai.OpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        
        response = client.chat.completions.create(
            model="qwen-plus",
            messages=[
                {
                    "role": "system",
                    "content": """你是一个查询增强助手。将用户的材料科学问题转换为适合检索的中英文查询。

输出格式（JSON，不要其他内容）：
{"query_cn": "中文增强查询（融合同义词、别名）", "query_en": "English enhanced query (with synonyms)"}

示例：
用户问题：TiAlN涂层的制备工艺
输出：{"query_cn": "TiAlN涂层 钛铝氮 制备工艺 沉积方法 PVD CVD 磁控溅射 电弧离子镀", "query_en": "TiAlN coating deposition process PVD CVD magnetron sputtering cathodic arc ion plating"}"""
                },
                {"role": "user", "content": question}
            ],
            temperature=0.3,
            max_tokens=300
        )
        
        import json
        result = json.loads(response.choices[0].message.content.strip())
        query_cn = result.get("query_cn", question)
        query_en = result.get("query_en", question)
        
        logger.info(f"[RAG] 查询增强 - 中文: {query_cn[:50]}...")
        logger.info(f"[RAG] 查询增强 - 英文: {query_en[:50]}...")
        
        return query_cn, query_en
        
    except Exception as e:
        logger.warning(f"[RAG] 查询增强失败，使用原始查询: {e}")
        return question, question


def get_client() -> Optional[MilvusClient]:
    """
    获取 Milvus 客户端单例
    """
    global _client
    
    if not RAG_AVAILABLE:
        return None
    
    if _client is None:
        try:
            _client = get_milvus_client()
            logger.info("Milvus 客户端初始化成功")
        except Exception as e:
            logger.error(f"Milvus 客户端初始化失败: {e}")
            return None
    
    return _client


def _format_single_doc(doc: SearchResult, ref_id: int) -> str:
    """
    格式化单个文档，返回结构化元数据
    
    数据库字段：
    - title: 文档标题
    - doc_type: 文档类型 (paper/patent/chinese_doc/english_doc)
    - page_num: 页码
    - metadata: JSON 字符串（可能包含 author、doi 等）
    - materials: 涉及的材料
    - processes: 涉及的工艺
    
    参数:
        doc: 检索结果
        ref_id: 引用编号
        
    返回:
        str: 格式化的文献内容
    """
    import json
    
    # 从数据库字段提取信息
    title = doc.metadata.get("title", "") or ""
    doc_type = doc.metadata.get("doc_type", "") or ""
    page_num = doc.metadata.get("page_num", "")
    materials = doc.metadata.get("materials", "") or ""
    processes = doc.metadata.get("processes", "") or ""
    
    # 解析 metadata JSON 字段（包含 author、doi 等额外信息）
    raw_metadata = doc.metadata.get("metadata", "")
    parsed_meta = {}
    if isinstance(raw_metadata, str) and raw_metadata.strip():
        try:
            parsed_meta = json.loads(raw_metadata)
        except json.JSONDecodeError:
            pass
    elif isinstance(raw_metadata, dict):
        parsed_meta = raw_metadata
    
    # 从 metadata JSON 中提取作者和 DOI
    authors = (
        parsed_meta.get("authors") or 
        parsed_meta.get("author") or 
        parsed_meta.get("作者") or 
        ""
    )
    doi = (
        parsed_meta.get("doi") or 
        parsed_meta.get("DOI") or 
        ""
    )
    
    # 处理作者列表格式
    if isinstance(authors, list):
        authors = ", ".join(str(a) for a in authors[:3])
        if len(authors) > 3:
            authors += " 等"
    
    # 内容
    content = doc.content.strip()
    
    # 判断语言（基于 doc_type 或 collection 来源）
    is_english = "english" in doc_type.lower() or (
        title and all(ord(c) < 128 for c in title.replace(" ", "").replace("-", "").replace(",", "")[:20])
    )
    lang_tag = "[EN]" if is_english else "[CN]"
    
    # 构建学术引用格式
    # 格式：[编号][语言] 作者. 标题. DOI: xxx
    lines = []
    
    # 引用信息行（学术格式，带语言标识，使用 • 而非 [n] 避免 LLM 混淆）
    citation_parts = [f"**•** {lang_tag}"]
    if authors:
        citation_parts.append(f"{authors}.")
    if title:
        citation_parts.append(f"*{title}*.")
    if doi:
        citation_parts.append(f"DOI: {doi}")
    
    lines.append(" ".join(citation_parts))
    
    # 内容摘要
    lines.append(f"\n> {content[:500]}{'...' if len(content) > 500 else ''}\n")
    
    return "\n".join(lines)


@tool
def query_knowledge_base(question: str) -> str:
    """
    检索涂层材料知识库，返回相关文献内容。
    
    **适用场景**:
    - 涂层材料特性、原理、制备工艺（PVD、CVD、电弧离子镀等）
    - 科研问题、机理分析
    - 历史文献中的实验数据或结论
    
    **返回格式**: 结构化的文献检索结果，包含标题、页码和内容摘要。
    你需要基于这些检索结果来回答用户问题，并在回答中引用文献编号。
    
    Args:
        question: 检索问题
        
    Returns:
        相关文献的结构化内容（包含引用信息）
    """
    client = get_client()
    
    if not client:
        return "❌ 知识库连接不可用。请检查 Milvus 服务。"
    
    try:
        logger.info(f"[RAG] 原始查询: {question}")
        config = get_rag_config()
        
        # 1. 查询增强：生成中英文优化查询
        query_cn, query_en = _enhance_query(question)
        
        # 从配置读取检索数量（中英文分开）
        top_k_cn = config.top_k_cn
        top_k_en = config.top_k_en
        
        cn_docs = []
        en_docs = []
        
        # 2. 使用增强的中文查询检索中文集合（取 top_k_cn 条）
        try:
            cn_docs = client.search(
                query=query_cn,
                collection_name=config.chinese_collection,
                top_k=top_k_cn
            )
            logger.info(f"[RAG] 中文集合检索: {len(cn_docs)} 条")
        except Exception as e:
            logger.warning(f"[RAG] 中文检索失败: {e}")
        
        # 3. 使用增强的英文查询检索英文集合（取 top_k_en 条）
        try:
            en_docs = client.search(
                query=query_en,
                collection_name=config.english_collection,
                top_k=top_k_en
            )
            logger.info(f"[RAG] 英文集合检索: {len(en_docs)} 条")
        except Exception as e:
            logger.warning(f"[RAG] 英文检索失败: {e}")
        
        # 4. 合并结果
        all_docs = cn_docs + en_docs
        
        if not all_docs:
            return "未检索到相关文献。请尝试使用不同的关键词。"
        
        # 去重：基于标题和 DOI 双重去重，保留相关度最高的
        seen_titles = {}
        seen_dois = set()
        unique_docs = []
        
        for doc in all_docs:
            title = doc.metadata.get("title", "").strip().lower()
            # 提取 DOI（可能在 metadata JSON 中）
            raw_meta = doc.metadata.get("metadata", "")
            doi = ""
            if isinstance(raw_meta, str) and raw_meta.strip():
                try:
                    import json
                    parsed = json.loads(raw_meta)
                    doi = (parsed.get("doi") or parsed.get("DOI") or "").strip().lower()
                except:
                    pass
            elif isinstance(raw_meta, dict):
                doi = (raw_meta.get("doi") or raw_meta.get("DOI") or "").strip().lower()
            
            # DOI 去重
            if doi and doi in seen_dois:
                continue
            
            # 标题去重
            if title and title in seen_titles:
                if doc.score > seen_titles[title].score:
                    unique_docs = [d for d in unique_docs if d.metadata.get("title", "").strip().lower() != title]
                    unique_docs.append(doc)
                    seen_titles[title] = doc
                    if doi:
                        seen_dois.add(doi)
            else:
                unique_docs.append(doc)
                if title:
                    seen_titles[title] = doc
                if doi:
                    seen_dois.add(doi)
        
        # 按相关度排序（不再限制数量，返回所有去重后的结果）
        unique_docs.sort(key=lambda x: x.score, reverse=True)
        
        logger.info(f"[RAG] 去重后: {len(unique_docs)} 条（中文 {len(cn_docs)} + 英文 {len(en_docs)} = {len(all_docs)}）")
        
        # 格式化输出
        output_parts = [
            f"# 检索结果（共 {len(unique_docs)} 条）",
            f"**原始查询**: {question}",
            f"**中文增强**: {query_cn[:80]}{'...' if len(query_cn) > 80 else ''}",
            f"**英文增强**: {query_en[:80]}{'...' if len(query_en) > 80 else ''}",
            ""
        ]
        
        for i, doc in enumerate(unique_docs, 1):
            output_parts.append(_format_single_doc(doc, i))
        
        # 格式提示
        output_parts.append("""
---
**输出要求**：
- 引用编号从 [1] 开始连续重编（不要使用原编号）
- 参考文献统一格式：`[编号] 作者. *标题*. DOI: xxx`
- 标题用斜体（`*标题*`），中英文格式一致
- 缺失 DOI 则省略 DOI 部分
""")
        
        return "\n".join(output_parts)
        
    except Exception as e:
        logger.error(f"[RAG] 检索失败: {e}")
        return f"检索过程中发生错误: {str(e)}"
