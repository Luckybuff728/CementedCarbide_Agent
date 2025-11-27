"""
历史数据服务 - 历史案例检索与比对
"""
from typing import Dict, Any, List
import logging
import time

logger = logging.getLogger(__name__)


class HistoricalDataService:
    """历史数据服务 - 检索相似案例"""
    
    def __init__(self):
        self.vector_db = None  # TODO: 接入向量数据库
    
    def retrieve_similar_cases(
        self, 
        composition: Dict, 
        params: Dict
    ) -> Dict[str, Any]:
        """
        检索历史相似案例
        
        Args:
            composition: 涂层成分
            params: 工艺参数
        
        Returns:
            历史数据比对结果
        """
        logger.info(f"[历史数据] 开始检索 - Al={composition.get('al_content')}%, "
                   f"Ti={composition.get('ti_content')}%, N={composition.get('n_content')}%")
        
        # 模拟数据库检索时间
        time.sleep(3)
        
        # TODO: 接入RAG系统 - 向量数据库检索
        # similar_cases = await rag_retrieve(
        #     query_embedding=self._encode_composition(composition),
        #     top_k=5
        # )
        
        # 当前使用示例数据模拟
        similar_cases = self._generate_mock_cases(composition)
        
        # 构建返回结果
        historical_comparison = {
            "similar_cases": similar_cases,
            "total_cases": len(similar_cases),
            "highest_hardness": max(c["hardness"] for c in similar_cases) if similar_cases else 0,
            "average_similarity": sum(c["similarity"] for c in similar_cases) / len(similar_cases) if similar_cases else 0
        }
        
        logger.info(f"[历史数据] 完成 - 找到 {len(similar_cases)} 个相似案例")
        
        return historical_comparison
    
    def _generate_mock_cases(self, composition: Dict) -> List[Dict]:
        """生成模拟历史案例数据
        
        注意：字段名与实验数据录入保持一致，方便前端对比展示
        - hardness: 硬度 (GPa)
        - adhesion_strength: 结合力 (N)
        - oxidation_temperature: 抗氧化温度 (℃)
        - wear_rate: 磨损率 (mm³/Nm)
        - surface_roughness: 表面粗糙度 (μm)
        
        TODO: 后续接入数据库，从历史实验记录表中检索相似案例
        """
        al_content = composition.get('al_content', 30)
        ti_content = composition.get('ti_content', 30)
        n_content = composition.get('n_content', 40)
        
        # 生成3个相似案例（字段名与实验数据一致）
        cases = [
            {
                "case_id": "CASE_001",
                "composition": {
                    "al_content": al_content + 2,
                    "ti_content": ti_content - 2,
                    "n_content": n_content
                },
                # 性能指标（与实验录入字段一致）
                "hardness": 29.2,
                "elastic_modulus": 440.0,
                "adhesion_strength": 55.3,
                "oxidation_temperature": 850,
                "wear_rate": 0.012,
                "surface_roughness": 0.15,
                # 元数据
                "similarity": 0.87,
                "notes": "相似成分配比，硬度表现良好",
                "year": "2023"
            },
            {
                "case_id": "CASE_002",
                "composition": {
                    "al_content": al_content + 5,
                    "ti_content": ti_content - 5,
                    "n_content": n_content
                },
                # 性能指标（与实验录入字段一致）
                "hardness": 31.1,
                "elastic_modulus": 470.0,
                "adhesion_strength": 58.7,
                "oxidation_temperature": 920,
                "wear_rate": 0.009,
                "surface_roughness": 0.12,
                # 元数据
                "similarity": 0.82,
                "notes": "高Al含量，显著提升硬度",
                "year": "2024"
            },
            {
                "case_id": "CASE_003",
                "composition": {
                    "al_content": al_content,
                    "ti_content": ti_content,
                    "n_content": n_content
                },
                # 性能指标（与实验录入字段一致）
                "hardness": 27.8,
                "elastic_modulus": 420.0,
                "adhesion_strength": 52.1,
                "oxidation_temperature": 820,
                "wear_rate": 0.015,
                "surface_roughness": 0.18,
                # 元数据
                "similarity": 0.75,
                "notes": "平衡配比，稳定性好",
                "year": "2023"
            }
        ]
        
        return cases
    
    def _calculate_similarity(self, comp1: Dict, comp2: Dict) -> float:
        """计算成分相似度（简化版）"""
        # 欧氏距离
        al_diff = abs(comp1.get('al_content', 0) - comp2.get('al_content', 0))
        ti_diff = abs(comp1.get('ti_content', 0) - comp2.get('ti_content', 0))
        n_diff = abs(comp1.get('n_content', 0) - comp2.get('n_content', 0))
        
        distance = (al_diff ** 2 + ti_diff ** 2 + n_diff ** 2) ** 0.5
        
        # 转换为相似度（0-1）
        max_distance = 100 * (3 ** 0.5)  # 最大距离
        similarity = 1 - (distance / max_distance)
        
        return round(similarity, 2)
