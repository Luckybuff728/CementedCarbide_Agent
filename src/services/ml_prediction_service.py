"""
ML模型预测服务 - 基于机器学习模型的性能预测
"""
from typing import Dict, Any
import time
from loguru import logger
import httpx



class MLPredictionService:
    """ML模型预测服务 - 性能预测"""
    
    def __init__(self):
        self.model_cache = {}  # TODO: 加载预训练模型
    
    def predict_performance(
        self, 
        composition: Dict, 
        params: Dict, 
        structure: Dict
    ) -> Dict[str, Any]:
        """
        ML模型预测 - 预测涂层性能
        
        Args:
            composition: 涂层成分
            params: 工艺参数
            structure: 结构设计
        
        Returns:
            性能预测结果
        """
        logger.info(f"[ML预测] 开始 - Al={composition.get('al_content')}%, Ti={composition.get('ti_content')}%")
        logger.info(f"[ML预测] 温度={params.get('deposition_temperature')}°C")
        
        # 模拟预测计算时间
        time.sleep(3)
        
        # TODO: 接入MCP工具 - ML预测服务
        # mcp_result = await call_mcp_tool("ml_predict", {
        #     "composition": composition,
        #     "params": params,
        #     "structure": structure
        # })
        
        # 当前使用示例数据模拟
        # 注意：核心性能指标与实验数据录入保持一致，便于前端统一展示
        predicted_hardness = None
        try:
            predicted_hardness = self._predict_hardness_via_onnx(composition, params)
        except Exception as e:
            logger.error(f"[ML预测] 硬度ONNX接口调用异常: {str(e)}")
        if predicted_hardness is None:
            predicted_hardness = self._predict_hardness(composition, params)
        predicted_elastic_modulus = self._predict_elastic_modulus(predicted_hardness)
        predicted_oxidation = self._predict_oxidation_temp(composition)
        
        ml_prediction = {
            # 4 个核心性能指标
            "hardness": predicted_hardness,
            "elastic_modulus": predicted_elastic_modulus,
            "wear_rate": self._predict_wear_rate(composition),
            "adhesion_strength": self._predict_adhesion_strength(composition, structure),
            
            # 可选附加指标（不纳入统一对比结构）
            "oxidation_temperature": predicted_oxidation,
            "surface_roughness": self._predict_surface_roughness(params),
            
            # 模型元数据
            "model_confidence": 0.8500
        }
        
        logger.info(f"[ML预测] 完成 - 硬度: {predicted_hardness:.4f} GPa, 弹性模量: {predicted_elastic_modulus:.4f} GPa")
        
        return ml_prediction
    
    def _predict_hardness(self, composition: Dict, params: Dict) -> float:
        """预测硬度（简化模型）"""
        # 基础硬度
        base_hardness = 25.0
        
        # Al含量影响（Al含量越高，硬度越高）
        al_content = composition.get('al_content') or 0
        al_factor = 1.0 + (al_content / 100) * 0.3
        
        # 温度影响
        temp = params.get('deposition_temperature') or 450
        temp_factor = 1.0 + (temp - 500) / 1000 * 0.1
        
        return round(base_hardness * al_factor * temp_factor, 4)

    def _predict_hardness_via_onnx(self, composition: Dict, params: Dict) -> float | None:
        """通过ONNX推理服务预测硬度"""
        al_content = (composition.get('al_content', 0) or 0) / 100.0
        ti_content = (composition.get('ti_content', 0) or 0) / 100.0
        n_content = (composition.get('n_content', 0) or 0) / 100.0

        # time_value = float(params.get('deposition_time', 100.0) or 100.0)
        # temperature = float(params.get('deposition_temperature', 500.0) or 500.0)
        time_value = 150.0
        temperature = 900.0

        # time_value = max(0.0, min(time_value, 500.0))
        # temperature = max(0.0, min(temperature, 1200.0))
        logger.info(f"[ML预测参数]  Al: {al_content} , Ti: {ti_content} , N: {n_content}, 处理时间: {time_value} , 温度: {temperature} ")
        url = "http://111.22.21.99:10002/models/70470382-7108-4f92-ad86-69b971f820cb/inference"
        payload = {
            "inputs": {
                "ti": ti_content,
                "al": al_content,
                "N": n_content,
                "time": time_value,
                "temperature": temperature,
            }
        }

        logger.info(f"[ML预测] 调用ONNX硬度预测服务: url={url}, payload={payload}")

        try:
            response = httpx.post(url, json=payload, timeout=5.0)
        except Exception as e:
            logger.error(f"[ML预测] ONNX服务请求失败: {str(e)}")
            return None

        if response.status_code != 200:
            logger.error(f"[ML预测] ONNX服务返回错误状态码: {response.status_code}")
            return None

        try:
            data = response.json()
            outputs = data.get("outputs", {})
            hardness_obj = outputs.get("hardness", {})
            hardness_value = hardness_obj.get("value")
        except Exception as e:
            logger.error(f"[ML预测] 解析ONNX服务响应失败: {str(e)}")
            return None

        if hardness_value is None:
            logger.error("[ML预测] ONNX服务响应中缺少硬度值")
            return None

        try:
            hardness = float(hardness_value)
        except (TypeError, ValueError) as e:
            logger.error(f"[ML预测] 硬度值转换失败: {str(e)}")
            return None

        hardness = round(hardness, 4)
        logger.info(f"[ML预测] ONNX硬度预测结果: {hardness:.4f}")
        return hardness

    def _predict_elastic_modulus(self, hardness: float) -> float:
        """预测弹性模量（GPa） - 简化模型，与硬度相关联"""
        # 经验比值：弹性模量通常是硬度的若干倍
        base_ratio = 15.0
        return round(hardness * base_ratio, 4)
    
    def _predict_adhesion_level(self, composition: Dict, structure: Dict) -> str:
        """预测结合力等级（保留旧方法名）"""
        thickness = structure.get('total_thickness', 0)
        
        if thickness < 2:
            return "HF1"
        elif thickness < 5:
            return "HF2"
        else:
            return "HF3"
    
    def _predict_adhesion_strength(self, composition: Dict, structure: Dict) -> float:
        """预测结合力数值（N）- 与实验数据字段统一
        
        TODO: 接入真实ML模型预测结合力
        """
        # 简化模型：基于Al含量和总厚度
        al_content = composition.get('al_content') or 30
        thickness = structure.get('total_thickness') or 3
        
        # 基础结合力
        base_adhesion = 45.0
        
        # Al含量影响（Al含量越高，结合力越好）
        al_factor = 1.0 + (al_content - 30) / 100 * 0.3
        
        # 厚度影响（厚度适中最好）
        if thickness < 2:
            thickness_factor = 0.9
        elif thickness > 5:
            thickness_factor = 0.95
        else:
            thickness_factor = 1.1
        
        return round(base_adhesion * al_factor * thickness_factor, 4)
    
    def _predict_wear_rate(self, composition: Dict) -> float:
        """预测磨损率"""
        # 简化：Al含量越高，磨损率越低
        al_content = composition.get('al_content') or 0
        base_rate = 2.0e-6
        
        return round(base_rate * (1 - al_content / 200), 4)
    
    def _predict_oxidation_temp(self, composition: Dict) -> float:
        """预测抗氧化温度（℃）
        
        TODO: 接入真实ML模型预测抗氧化温度
        """
        # 简化：Al含量越高，抗氧化性越好
        al_content = composition.get('al_content') or 0
        base_temp = 700
        
        return round(base_temp + al_content * 3, 4)
    
    def _predict_surface_roughness(self, params: Dict) -> float:
        """预测表面粗糙度（μm）- 与实验数据字段统一
        
        TODO: 接入真实ML模型预测表面粗糙度
        """
        # 简化模型：基于沉积温度和偏压
        temp = params.get('deposition_temperature') or 450
        bias = abs(params.get('bias_voltage') or -100)
        
        # 基础粗糙度
        base_roughness = 0.2
        
        # 温度影响（温度越高，粗糙度越低）
        temp_factor = 1.0 - (temp - 400) / 1000 * 0.3
        
        # 偏压影响（偏压越大，粗糙度越低）
        bias_factor = 1.0 - (bias - 50) / 200 * 0.2
        
        roughness = base_roughness * temp_factor * bias_factor
        
        return round(max(0.05, roughness), 4)
