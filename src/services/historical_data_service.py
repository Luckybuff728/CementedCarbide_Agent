"""
历史数据服务 - 基于 RAG + LLM 的智能历史案例检索

功能:
- LLM 查询增强：根据涂层参数智能生成检索查询
- RAG 向量检索：从知识库检索相关文献
- LLM 结果处理：智能提取和结构化性能数据
- 返回 Markdown 格式的分析报告
"""
from typing import Dict, Any, List, Optional
import os
import json
from loguru import logger

# 尝试导入 RAG 模块
try:
    from src.rag import get_milvus_client, get_rag_config
    from src.rag.milvus_client import SearchResult
    RAG_AVAILABLE = True
except ImportError as e:
    logger.warning(f"RAG 模块导入失败: {e}")
    RAG_AVAILABLE = False


class HistoricalDataService:
    """
    历史数据服务 - 基于 RAG + LLM 的智能检索
    
    工作流程:
    1. LLM 查询增强：将用户参数转换为优化的检索查询
    2. RAG 检索：从 Milvus 向量数据库检索相关文献
    3. LLM 结果处理：从检索结果中提取结构化数据并生成分析
    """
    
    def __init__(self):
        """初始化历史数据服务"""
        self._milvus_client = None
        self._config = None
        self._llm_client = None
    
    def _get_llm_client(self):
        """
        获取 LLM 客户端（懒加载）
        """
        if self._llm_client is None:
            import openai
            self._llm_client = openai.OpenAI(
                api_key=os.getenv("DASHSCOPE_API_KEY"),
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
            )
        return self._llm_client
    
    def _get_rag_client(self, max_retries: int = 3, retry_delay: float = 2.0):
        """
        获取 RAG 客户端（懒加载，带重试机制）
        
        参数:
            max_retries: 最大重试次数
            retry_delay: 重试间隔（秒）
        """
        import time
        
        if not RAG_AVAILABLE:
            return None, None
        
        # 如果已有客户端且连接正常，直接返回
        if self._milvus_client is not None:
            try:
                # 测试连接是否有效
                from pymilvus import connections
                if connections.has_connection("default"):
                    return self._milvus_client, self._config
            except Exception:
                # 连接失效，重新创建
                self._milvus_client = None
        
        # 重试创建客户端
        for attempt in range(max_retries):
            try:
                self._config = get_rag_config()
                self._milvus_client = get_milvus_client()
                logger.info("[历史数据] RAG 客户端初始化成功")
                return self._milvus_client, self._config
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"[历史数据] RAG 客户端初始化失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"[历史数据] RAG 客户端初始化失败 (已重试 {max_retries} 次): {e}")
        
        return None, None
    
    def _llm_enhance_query(
        self, 
        composition: Dict, 
        params: Dict,
        target_requirements: Optional[Dict] = None
    ) -> Dict[str, str]:
        """
        使用 LLM 增强检索查询
        
        参数:
            composition: 涂层成分
            params: 工艺参数
            target_requirements: 性能需求
        
        返回:
            Dict: {"query_cn": 中文查询, "query_en": 英文查询}
        """
        # 构建用户参数描述
        param_desc = f"""
涂层成分:
- Al含量: {composition.get('al_content', 'N/A')}%
- Ti含量: {composition.get('ti_content', 'N/A')}%
- N含量: {composition.get('n_content', 'N/A')}%

工艺参数:
- 工艺类型: {params.get('process_type', 'N/A')}
- 沉积温度: {params.get('deposition_temperature', 'N/A')}°C
- 沉积气压: {params.get('deposition_pressure', 'N/A')} Pa
- 偏压: {params.get('bias_voltage', 'N/A')} V
"""
        if target_requirements:
            param_desc += f"""
性能需求:
- 工作温度: {target_requirements.get('working_temperature', 'N/A')}°C
- 应用场景: {target_requirements.get('application_scenario', 'N/A')}
"""
        
        try:
            client = self._get_llm_client()
            response = client.chat.completions.create(
                model="qwen-plus",
                messages=[
                    {
                        "role": "system",
                        "content": """你是涂层材料检索专家。根据用户的涂层参数，生成优化的中英文检索查询。

要求:
1. 查询应包含涂层类型（TiAlN/AlTiN）、关键参数、相关性能指标
2. 融入专业术语和同义词以提高召回率
3. 中文查询侧重国内文献风格，英文查询侧重国际论文风格

输出格式（严格JSON，不要其他内容）:
{"query_cn": "中文检索查询", "query_en": "English search query"}"""
                    },
                    {"role": "user", "content": param_desc}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            result = json.loads(response.choices[0].message.content.strip())
            logger.info(f"[历史数据] LLM 查询增强完成")
            return result
            
        except Exception as e:
            logger.warning(f"[历史数据] LLM 查询增强失败: {e}")
            # 降级：简单拼接
            al = composition.get('al_content', 30)
            return {
                "query_cn": f"TiAlN涂层 Al{al}% 硬度 性能 工艺参数",
                "query_en": f"TiAlN coating Al{al}% hardness performance"
            }
    
    def _llm_analyze_results(
        self,
        raw_results: List[SearchResult],
        composition: Dict,
        params: Dict,
        structure_design: Optional[Dict],
        target_requirements: Optional[Dict]
    ) -> Dict[str, Any]:
        """
        使用 LLM 分析和结构化检索结果
        
        参数:
            raw_results: RAG 检索的原始结果
            composition: 用户输入的涂层成分
            params: 用户输入的工艺参数
            structure_design: 用户输入的结构设计
            target_requirements: 用户的性能需求
        
        返回:
            Dict: 结构化的分析结果
        """
        # 准备检索内容摘要
        docs_summary = []
        for i, result in enumerate(raw_results[:8], 1):
            title = result.metadata.get("title", f"文献{i}")
            content = result.content[:800]  # 限制长度
            docs_summary.append(f"【文献{i}】{title}\n{content}")
        
        docs_text = "\n\n".join(docs_summary)
        
        # 用户参数描述（参考前端 useMultiAgent.js 的参数结构）
        # 工艺类型映射
        process_type_map = {
            'magnetron_sputtering': '磁控溅射',
            'arc_ion_plating': '电弧离子镀',
            'cvd': 'CVD',
            'pecvd': 'PECVD',
            'hipims': 'HiPIMS'
        }
        
        # 结构类型映射
        struct_type_map = {
            'single': '单层',
            'multi': '多层',
            'gradient': '梯度',
            'nano_multilayer': '纳米多层'
        }
        
        user_params = "用户涂层配置:\n\n"
        
        # 【涂层成分】
        user_params += "【涂层成分】\n"
        al = composition.get('al_content', 0) or 0
        ti = composition.get('ti_content', 0) or 0
        n = composition.get('n_content', 0) or 0
        user_params += f"- 成分配比: Al {al}%, Ti {ti}%, N {n}%\n"
        
        # 其他元素
        other_elements = composition.get('other_elements', [])
        if other_elements and isinstance(other_elements, list) and len(other_elements) > 0:
            other_str = ', '.join([f"{e.get('name', '')} {e.get('content', 0)}%" for e in other_elements if e.get('name')])
            if other_str:
                user_params += f"- 其他元素: {other_str}\n"
        
        # 【工艺参数】
        user_params += "\n【工艺参数】\n"
        process_type = params.get('process_type', 'magnetron_sputtering')
        process_type_cn = process_type_map.get(process_type, process_type or '磁控溅射')
        user_params += f"- 工艺类型: {process_type_cn}\n"
        user_params += f"- 沉积温度: {params.get('deposition_temperature', 'N/A')}°C\n"
        user_params += f"- 沉积压力: {params.get('deposition_pressure', 'N/A')} Pa\n"
        user_params += f"- 偏压: {params.get('bias_voltage', 'N/A')} V\n"
        user_params += f"- N₂流量: {params.get('n2_flow', 'N/A')} sccm\n"
        
        # 其他气体
        other_gases = params.get('other_gases', [])
        if other_gases and isinstance(other_gases, list) and len(other_gases) > 0:
            gas_str = ', '.join([f"{g.get('type', '')} {g.get('flow', 0)}sccm" for g in other_gases if g.get('type')])
            if gas_str:
                user_params += f"- 其他气体: {gas_str}\n"
        
        # 【结构设计】（如果有）
        structure = structure_design or {}
        if structure:
            user_params += "\n【结构设计】\n"
            struct_type = structure.get('structure_type', 'single')
            struct_type_cn = struct_type_map.get(struct_type, struct_type or '单层')
            user_params += f"- 结构类型: {struct_type_cn}\n"
            user_params += f"- 总厚度: {structure.get('total_thickness', 'N/A')} μm\n"
            
            layers = structure.get('layers', [])
            if layers and isinstance(layers, list) and len(layers) > 0:
                layer_str = ' → '.join([f"{l.get('type', '')} {l.get('thickness', 0)}μm" for l in layers])
                if layer_str:
                    user_params += f"- 层结构: {layer_str}\n"
        
        # 【性能目标】
        if target_requirements and isinstance(target_requirements, dict):
            user_params += "\n【性能目标】\n"
            if target_requirements.get('substrate_material'):
                user_params += f"- 基材: {target_requirements.get('substrate_material')}\n"
            if target_requirements.get('adhesion_strength'):
                user_params += f"- 结合力要求: ≥{target_requirements.get('adhesion_strength')} N\n"
            if target_requirements.get('elastic_modulus'):
                user_params += f"- 弹性模量要求: {target_requirements.get('elastic_modulus')} GPa\n"
            if target_requirements.get('hardness') or target_requirements.get('target_hardness'):
                hardness = target_requirements.get('hardness') or target_requirements.get('target_hardness')
                user_params += f"- 硬度要求: ≥{hardness} GPa\n"
            if target_requirements.get('working_temperature'):
                user_params += f"- 工作温度: {target_requirements.get('working_temperature')}°C\n"
            if target_requirements.get('cutting_speed'):
                user_params += f"- 切削速度: {target_requirements.get('cutting_speed')} m/min\n"
            if target_requirements.get('application_scenario'):
                user_params += f"- 应用场景: {target_requirements.get('application_scenario')}\n"
        
        try:
            client = self._get_llm_client()
            response = client.chat.completions.create(
                model="qwen-plus",
                messages=[
                    {
                        "role": "system",
                        "content": """你是涂层材料分析专家。从检索到的文献中提取与用户配置相关的关键数据和见解。

任务:
1. **仔细提取**文献中的具体性能数据（硬度、弹性模量、结合力、磨损率等）
2. 找出与用户配置相似的案例
3. 总结对用户配置有参考价值的关键发现
4. 提供基于文献的改进建议

**重要**：尽可能提取完整的四项性能指标（请仔细查找文献中的数值）：
- hardness: 硬度，单位统一为 GPa（如 HV 值需除以约100转换，如 3000 HV ≈ 30 GPa）
- elastic_modulus: 弹性模量/杨氏模量/Young's modulus，单位 GPa
- adhesion_strength: 结合力/附着力/临界载荷/Lc，单位 N
- wear_rate: 磨损率/比磨损率/wear coefficient，单位 mm³/Nm 或 10^-6 mm³/Nm

**提取技巧**：
- 硬度可能表示为 HV、GPa、纳米硬度等
- 弹性模量可能在纳米压痕测试结果中
- 结合力可能表示为划痕测试的临界载荷 Lc
- 磨损率可能表示为比磨损率、磨损系数等

输出格式（严格JSON）:
{
    "performance_data": [
        {
            "source": "文献标题或编号",
            "composition": "涂层成分描述（如 Ti0.5Al0.5N）",
            "process": "工艺条件（如 PVD, 450°C）",
            "hardness": 数值(GPa)或null,
            "elastic_modulus": 数值(GPa)或null,
            "adhesion_strength": 数值(N)或null,
            "wear_rate": 数值(mm³/Nm)或null,
            "notes": "其他备注信息或原始数据单位说明"
        }
    ],
    "key_findings": [
        "发现1: 具体描述",
        "发现2: 具体描述"
    ],
    "recommendations": [
        "建议1: 基于文献的具体建议",
        "建议2: 基于文献的具体建议"
    ],
    "relevance_summary": "与用户配置的相关性总结（1-2句话）"
}

注意：
- 数值请直接填写数字，不要带单位
- 如果文献中没有明确数据，填 null
- 优先提取与用户成分配比最接近的案例
- 尽量从每篇文献中提取尽可能多的指标"""
                    },
                    {
                        "role": "user", 
                        "content": f"{user_params}\n\n检索到的相关文献:\n{docs_text}"
                    }
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            result = json.loads(response.choices[0].message.content.strip())
            logger.info(f"[历史数据] LLM 结果分析完成")
            return result
            
        except Exception as e:
            logger.error(f"[历史数据] LLM 分析失败: {e}")
            # 降级：返回基础信息
            return {
                "performance_data": [],
                "key_findings": ["LLM 分析暂时不可用，请查看原始检索结果"],
                "recommendations": [],
                "relevance_summary": "检索完成，但智能分析暂时不可用"
            }
    
    def retrieve_similar_cases(
        self, 
        composition: Dict, 
        params: Dict,
        structure_design: Optional[Dict] = None,
        target_requirements: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        检索历史相似案例（LLM 增强版）
        
        工作流程:
        1. LLM 增强查询
        2. RAG 向量检索
        3. LLM 结果分析
        
        参数:
            composition: 涂层成分
            params: 工艺参数
            target_requirements: 性能需求
        
        返回:
            Dict: 包含分析报告和结构化数据
        """
        logger.info(f"[历史数据] 开始智能检索 - Al={composition.get('al_content')}%")
        
        # 获取 RAG 客户端
        client, config = self._get_rag_client()
        if not client or not config:
            logger.warning("[历史数据] RAG 不可用")
            return self._generate_fallback_result(composition)
        
        try:
            # Step 1: LLM 查询增强
            queries = self._llm_enhance_query(composition, params, target_requirements)
            query_cn = queries.get("query_cn", "")
            query_en = queries.get("query_en", "")
            
            # Step 2: RAG 检索（分别标记中英文来源）
            cn_results = []
            en_results = []
            
            # 中文检索
            try:
                cn_results = client.search(
                    query=query_cn,
                    collection_name=config.chinese_collection,
                    top_k=8
                )
                # 标记语言
                for r in cn_results:
                    r.metadata["language"] = "zh"
                logger.info(f"[历史数据] 中文检索: {len(cn_results)} 条")
            except Exception as e:
                logger.warning(f"[历史数据] 中文检索失败: {e}")
            
            # 英文检索
            try:
                en_results = client.search(
                    query=query_en,
                    collection_name=config.english_collection,
                    top_k=5
                )
                # 标记语言
                for r in en_results:
                    r.metadata["language"] = "en"
                logger.info(f"[历史数据] 英文检索: {len(en_results)} 条")
            except Exception as e:
                logger.warning(f"[历史数据] 英文检索失败: {e}")
            
            # 合并结果
            all_results = cn_results + en_results
            
            if not all_results:
                return self._generate_fallback_result(composition)
            
            # 按相关度排序
            all_results.sort(key=lambda x: x.score, reverse=True)
            
            # Step 3: LLM 分析结果
            analysis = self._llm_analyze_results(
                all_results, composition, params, structure_design, target_requirements
            )
            
            # 构建文献引用（确保中英文都有代表）
            # 按语言分组，各取前几条
            cn_refs = [r for r in all_results if r.metadata.get("language") == "zh"][:5]
            en_refs = [r for r in all_results if r.metadata.get("language") == "en"][:3]
            ref_results = cn_refs + en_refs
            # 按相关度重新排序
            ref_results.sort(key=lambda x: x.score, reverse=True)
            
            # 构建最终结果
            result = {
                # 核心分析数据（供 LLM 和前端展示）
                "performance_data": analysis.get("performance_data", []),
                "key_findings": analysis.get("key_findings", []),
                "recommendations": analysis.get("recommendations", []),
                "relevance_summary": analysis.get("relevance_summary", ""),
                
                # 关键性能指标（供后续实验对比使用）
                "extracted_metrics": self._extract_key_metrics(analysis.get("performance_data", [])),
                
                # 元数据
                "total_docs_retrieved": len(all_results),
                "cn_docs_count": len(cn_results),
                "en_docs_count": len(en_results),
                "data_source": "RAG+LLM",
                "search_queries": {
                    "chinese": query_cn,
                    "english": query_en
                },
                
                # 原始文献引用（学术论文格式）
                "references": [
                    self._format_reference(r) for r in ref_results
                ]
            }
            
            logger.info(f"[历史数据] 智能检索完成 - {len(all_results)} 篇文献")
            return result
            
        except Exception as e:
            logger.error(f"[历史数据] 检索失败: {e}")
            return self._generate_fallback_result(composition)
    
    def _format_reference(self, result) -> Dict[str, Any]:
        """
        格式化文献引用为学术论文格式
        
        格式: 作者. 标题. DOI: xxx
        示例: 张三 等. TiAlN涂层制备工艺研究. DOI: 10.1016/xxx
        
        参数:
            result: RAG 检索结果对象
        
        返回:
            Dict: 格式化的引用信息
        """
        import json
        
        metadata = result.metadata
        title = metadata.get("title", "未知标题")
        language = metadata.get("language", "zh")
        doc_type = metadata.get("doc_type", "paper")
        
        # 解析嵌套的 metadata JSON
        authors = []
        doi = ""
        try:
            nested_meta = metadata.get("metadata", "")
            if nested_meta and isinstance(nested_meta, str):
                parsed = json.loads(nested_meta)
                authors = parsed.get("authors", [])
                doi = parsed.get("doi", "")
        except (json.JSONDecodeError, TypeError):
            pass
        
        # 格式化作者
        if authors:
            if language == "zh":
                # 中文：第一作者 等
                author_str = f"{authors[0]} 等" if len(authors) > 1 else authors[0]
            else:
                # 英文：First Author, et al.
                author_str = f"{authors[0]}, et al." if len(authors) > 1 else authors[0]
        else:
            author_str = ""
        
        # 构建格式化引用字符串
        # 格式: 作者. 标题. DOI: xxx
        citation_parts = []
        if author_str:
            citation_parts.append(author_str)
        citation_parts.append(title)
        if doi:
            citation_parts.append(f"DOI: {doi}")
        
        citation = ". ".join(citation_parts)
        
        return {
            "citation": citation,
            "title": title,
            "authors": authors,
            "doi": doi,
            "doc_type": doc_type,
            "language": language,
            "relevance_score": round(result.score, 4)
        }
    
    def _extract_key_metrics(self, performance_data: List[Dict]) -> Dict[str, Any]:
        """
        从性能数据中提取关键指标，供后续实验对比使用
        
        提取内容:
        - hardness: 硬度范围 (min, max, avg)
        - elastic_modulus: 弹性模量范围
        - adhesion_strength: 结合力范围
        - wear_rate: 磨损率范围
        - best_case: 最佳案例参考
        
        参数:
            performance_data: LLM 提取的性能数据列表
        
        返回:
            Dict: 关键指标汇总
        """
        hardness_values = []
        modulus_values = []
        adhesion_values = []
        wear_rate_values = []
        
        for item in performance_data:
            # 硬度：兼容多种字段名
            val = item.get("hardness") or item.get("hardness_gpa")
            if val:
                try:
                    hardness_values.append(float(val))
                except (ValueError, TypeError):
                    pass
            
            # 弹性模量：兼容多种字段名
            val = item.get("elastic_modulus") or item.get("modulus_gpa") or item.get("modulus")
            if val:
                try:
                    modulus_values.append(float(val))
                except (ValueError, TypeError):
                    pass
            
            # 结合力：兼容多种字段名
            val = item.get("adhesion_strength") or item.get("adhesion_n") or item.get("adhesion")
            if val:
                try:
                    adhesion_values.append(float(val))
                except (ValueError, TypeError):
                    pass
            
            # 磨损率
            val = item.get("wear_rate")
            if val:
                try:
                    wear_rate_values.append(float(val))
                except (ValueError, TypeError):
                    pass
        
        metrics = {}
        
        # 硬度指标
        if hardness_values:
            metrics["hardness"] = {
                "min": round(min(hardness_values), 2),
                "max": round(max(hardness_values), 2),
                "avg": round(sum(hardness_values) / len(hardness_values), 2),
                "count": len(hardness_values)
            }
        
        # 弹性模量指标
        if modulus_values:
            metrics["elastic_modulus"] = {
                "min": round(min(modulus_values), 2),
                "max": round(max(modulus_values), 2),
                "avg": round(sum(modulus_values) / len(modulus_values), 2),
                "count": len(modulus_values)
            }
        
        # 结合力指标
        if adhesion_values:
            metrics["adhesion_strength"] = {
                "min": round(min(adhesion_values), 2),
                "max": round(max(adhesion_values), 2),
                "avg": round(sum(adhesion_values) / len(adhesion_values), 2),
                "count": len(adhesion_values)
            }
        
        # 磨损率指标
        if wear_rate_values:
            metrics["wear_rate"] = {
                "min": round(min(wear_rate_values), 6),
                "max": round(max(wear_rate_values), 6),
                "avg": round(sum(wear_rate_values) / len(wear_rate_values), 6),
                "count": len(wear_rate_values)
            }
        
        # 最佳案例（硬度最高的）
        if hardness_values:
            max_hardness = max(hardness_values)
            for item in performance_data:
                try:
                    item_hardness = float(item.get("hardness") or item.get("hardness_gpa") or 0)
                    if item_hardness == max_hardness:
                        metrics["best_case"] = {
                            "source": item.get("source", ""),
                            "composition": item.get("composition", ""),
                            "hardness": max_hardness,
                            "elastic_modulus": item.get("elastic_modulus") or item.get("modulus_gpa"),
                            "adhesion_strength": item.get("adhesion_strength") or item.get("adhesion_n"),
                            "wear_rate": item.get("wear_rate")
                        }
                        break
                except (ValueError, TypeError):
                    pass
        
        return metrics
    
    def _generate_fallback_result(self, composition: Dict) -> Dict[str, Any]:
        """
        生成降级结果（RAG/LLM 不可用时）
        """
        return {
            "performance_data": [],
            "key_findings": ["知识库检索暂时不可用，无法提供历史案例参考"],
            "recommendations": ["建议稍后重试，或直接进行 ML 性能预测"],
            "relevance_summary": "服务暂时不可用",
            "extracted_metrics": {},
            "total_docs_retrieved": 0,
            "cn_docs_count": 0,
            "en_docs_count": 0,
            "data_source": "FALLBACK",
            "search_queries": {},
            "references": []
        }
    
