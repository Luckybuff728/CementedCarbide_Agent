"""
实验结果分析服务 - 对比分析与参数更新

功能：
1. 实验结果 vs 预测结果对比
2. 实验结果 vs 目标需求对比
3. 达标判断
4. 从优化建议中提取新参数
"""
from typing import Dict, Any, Optional, List, Tuple
import logging
import re

logger = logging.getLogger(__name__)


class ExperimentAnalysisService:
    """实验结果分析服务"""
    
    def __init__(self):
        # 性能指标及其目标方向（True=越大越好，False=越小越好）
        self.metrics_direction = {
            "hardness": True,           # 硬度：越大越好
            "elastic_modulus": True,    # 弹性模量：越大越好
            "wear_rate": False,         # 磨损率：越小越好
            "adhesion_strength": True,  # 结合力：越大越好
        }
        
        # 默认目标阈值（如果用户未指定）
        self.default_targets = {
            "hardness": 30.0,           # GPa
            "elastic_modulus": 350.0,   # GPa
            "wear_rate": 1e-6,          # mm³/Nm
            "adhesion_strength": 50.0,  # N
        }
    
    def analyze_experiment_results(
        self,
        experiment_data: Dict[str, Any],
        prediction_data: Dict[str, Any],
        target_requirements: Dict[str, Any],
        historical_best: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        综合分析实验结果
        
        Args:
            experiment_data: 用户输入的实验结果
            prediction_data: ML预测结果
            target_requirements: 目标需求
            historical_best: 历史最优数据（可选）
        
        Returns:
            分析结果，包含对比、达标判断、改进建议
        """
        logger.info("[实验分析] 开始综合分析...")
        
        # 1. 预测误差分析
        prediction_comparison = self._compare_with_prediction(
            experiment_data, prediction_data
        )
        
        # 2. 目标达成分析
        target_comparison = self._compare_with_target(
            experiment_data, target_requirements
        )
        
        # 3. 历史对比分析
        historical_comparison = None
        if historical_best:
            historical_comparison = self._compare_with_historical(
                experiment_data, historical_best
            )
        
        # 4. 综合达标判断
        is_target_met, unmet_metrics = self._check_target_met(
            experiment_data, target_requirements
        )
        
        # 5. 生成分析报告
        analysis_report = self._generate_analysis_report(
            experiment_data,
            prediction_comparison,
            target_comparison,
            historical_comparison,
            is_target_met,
            unmet_metrics
        )
        
        result = {
            "prediction_comparison": prediction_comparison,
            "target_comparison": target_comparison,
            "historical_comparison": historical_comparison,
            "is_target_met": is_target_met,
            "unmet_metrics": unmet_metrics,
            "analysis_report": analysis_report,
            "recommendation": "continue" if not is_target_met else "complete"
        }
        
        logger.info(f"[实验分析] 完成，达标={is_target_met}")
        return result
    
    def _compare_with_prediction(
        self,
        experiment: Dict[str, Any],
        prediction: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        对比实验结果与预测结果
        """
        comparison = {}
        
        for metric in self.metrics_direction.keys():
            exp_val = self._safe_float(experiment.get(metric))
            pred_val = self._safe_float(prediction.get(metric))
            
            if exp_val is not None and pred_val is not None and pred_val != 0:
                error = exp_val - pred_val
                error_rate = (error / pred_val) * 100
                
                comparison[metric] = {
                    "experiment": exp_val,
                    "prediction": pred_val,
                    "error": error,
                    "error_rate": round(error_rate, 2),
                    "accuracy": "准确" if abs(error_rate) < 10 else (
                        "偏高" if error > 0 else "偏低"
                    )
                }
        
        return comparison
    
    def _compare_with_target(
        self,
        experiment: Dict[str, Any],
        target: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        对比实验结果与目标需求
        """
        comparison = {}
        
        # 映射目标字段名到标准名
        target_mapping = {
            "hardness": ["hardness", "target_hardness"],
            "elastic_modulus": ["elastic_modulus", "target_elastic_modulus"],
            "wear_rate": ["wear_rate", "target_wear_rate"],
            "adhesion_strength": ["adhesion_strength", "bonding_strength", "target_adhesion"],
        }
        
        for metric, higher_better in self.metrics_direction.items():
            exp_val = self._safe_float(experiment.get(metric))
            
            # 查找目标值
            target_val = None
            for key in target_mapping.get(metric, [metric]):
                if target.get(key):
                    target_val = self._safe_float(target.get(key))
                    break
            
            # 使用默认目标
            if target_val is None:
                target_val = self.default_targets.get(metric)
            
            if exp_val is not None and target_val is not None:
                gap = exp_val - target_val
                gap_rate = (gap / target_val) * 100 if target_val != 0 else 0
                
                # 判断是否达标
                if higher_better:
                    met = exp_val >= target_val
                else:
                    met = exp_val <= target_val
                
                comparison[metric] = {
                    "experiment": exp_val,
                    "target": target_val,
                    "gap": gap,
                    "gap_rate": round(gap_rate, 2),
                    "met": met,
                    "status": "达标" if met else ("超出" if gap > 0 else "不足")
                }
        
        return comparison
    
    def _compare_with_historical(
        self,
        experiment: Dict[str, Any],
        historical: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        对比实验结果与历史最优
        """
        comparison = {}
        
        for metric, higher_better in self.metrics_direction.items():
            exp_val = self._safe_float(experiment.get(metric))
            hist_val = self._safe_float(historical.get(metric))
            
            if exp_val is not None and hist_val is not None:
                diff = exp_val - hist_val
                diff_rate = (diff / hist_val) * 100 if hist_val != 0 else 0
                
                # 判断是否有改进
                if higher_better:
                    improved = exp_val > hist_val
                else:
                    improved = exp_val < hist_val
                
                comparison[metric] = {
                    "experiment": exp_val,
                    "historical_best": hist_val,
                    "difference": diff,
                    "difference_rate": round(diff_rate, 2),
                    "improved": improved
                }
        
        return comparison
    
    def _check_target_met(
        self,
        experiment: Dict[str, Any],
        target: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        检查是否达标
        
        Returns:
            (是否全部达标, 未达标的指标列表)
        """
        target_comparison = self._compare_with_target(experiment, target)
        
        unmet = []
        for metric, data in target_comparison.items():
            if not data.get("met", True):
                unmet.append(metric)
        
        return len(unmet) == 0, unmet
    
    def _generate_analysis_report(
        self,
        experiment: Dict[str, Any],
        prediction_comparison: Dict[str, Any],
        target_comparison: Dict[str, Any],
        historical_comparison: Optional[Dict[str, Any]],
        is_target_met: bool,
        unmet_metrics: List[str]
    ) -> str:
        """
        生成分析报告文本
        """
        lines = ["## 实验结果分析报告\n"]
        
        # 总结
        if is_target_met:
            lines.append("### ✅ 综合评价：目标达成\n")
            lines.append("恭喜！本次实验结果已达到所有性能目标。\n")
        else:
            metric_names = {
                "hardness": "硬度",
                "elastic_modulus": "弹性模量",
                "wear_rate": "磨损率",
                "adhesion_strength": "结合力"
            }
            unmet_names = [metric_names.get(m, m) for m in unmet_metrics]
            lines.append("### ⚠️ 综合评价：部分指标未达标\n")
            lines.append(f"以下指标需要改进：**{', '.join(unmet_names)}**\n")
        
        # 预测对比
        lines.append("\n### 预测准确性分析\n")
        lines.append("| 指标 | 实验值 | 预测值 | 误差率 | 评价 |")
        lines.append("|------|--------|--------|--------|------|")
        
        metric_names = {
            "hardness": "硬度 (GPa)",
            "elastic_modulus": "弹性模量 (GPa)",
            "wear_rate": "磨损率 (mm³/Nm)",
            "adhesion_strength": "结合力 (N)"
        }
        
        for metric, data in prediction_comparison.items():
            name = metric_names.get(metric, metric)
            exp = f"{data['experiment']:.2f}" if metric != "wear_rate" else f"{data['experiment']:.2e}"
            pred = f"{data['prediction']:.2f}" if metric != "wear_rate" else f"{data['prediction']:.2e}"
            err = f"{data['error_rate']:+.1f}%"
            acc = data['accuracy']
            lines.append(f"| {name} | {exp} | {pred} | {err} | {acc} |")
        
        # 目标对比
        lines.append("\n### 目标达成分析\n")
        lines.append("| 指标 | 实验值 | 目标值 | 差距 | 状态 |")
        lines.append("|------|--------|--------|------|------|")
        
        for metric, data in target_comparison.items():
            name = metric_names.get(metric, metric)
            exp = f"{data['experiment']:.2f}" if metric != "wear_rate" else f"{data['experiment']:.2e}"
            tgt = f"{data['target']:.2f}" if metric != "wear_rate" else f"{data['target']:.2e}"
            gap = f"{data['gap_rate']:+.1f}%"
            status = "✅ " + data['status'] if data['met'] else "❌ " + data['status']
            lines.append(f"| {name} | {exp} | {tgt} | {gap} | {status} |")
        
        return "\n".join(lines)
    
    def extract_new_parameters_from_optimization(
        self,
        selected_type: str,
        optimization_content: str,
        current_composition: Dict[str, Any],
        current_process: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        从优化建议中提取新参数
        
        这是迭代的关键：用优化建议中的参数作为下一轮的输入
        
        Args:
            selected_type: 选择的优化类型 (P1/P2/P3)
            optimization_content: 优化建议的完整内容
            current_composition: 当前涂层成分
            current_process: 当前工艺参数
        
        Returns:
            提取的新参数（成分和工艺）
        """
        logger.info(f"[参数提取] 从 {selected_type} 优化建议中提取新参数...")
        
        new_composition = dict(current_composition)
        new_process = dict(current_process)
        
        # 解析优化内容中的参数表格
        # 通常格式：| 参数名称 | 当前值 | 优化值 | 调整原因 |
        
        # 提取Al含量
        al_match = re.search(r'Al含量.*?(\d+\.?\d*)\s*at\.?%.*?(\d+\.?\d*)\s*at\.?%', optimization_content)
        if al_match:
            new_composition["al_content"] = float(al_match.group(2))
            logger.info(f"[参数提取] Al含量: {current_composition.get('al_content')} → {new_composition['al_content']}")
        
        # 提取Ti含量
        ti_match = re.search(r'Ti含量.*?(\d+\.?\d*)\s*at\.?%.*?(\d+\.?\d*)\s*at\.?%', optimization_content)
        if ti_match:
            new_composition["ti_content"] = float(ti_match.group(2))
            logger.info(f"[参数提取] Ti含量: {current_composition.get('ti_content')} → {new_composition['ti_content']}")
        
        # 提取N含量
        n_match = re.search(r'N含量.*?(\d+\.?\d*)\s*at\.?%.*?(\d+\.?\d*)\s*at\.?%', optimization_content)
        if n_match:
            new_composition["n_content"] = float(n_match.group(2))
        
        # 提取沉积温度
        temp_match = re.search(r'沉积温度.*?(\d+)\s*°?C.*?(\d+)\s*°?C', optimization_content)
        if temp_match:
            new_process["deposition_temperature"] = int(temp_match.group(2))
            logger.info(f"[参数提取] 沉积温度: {current_process.get('deposition_temperature')} → {new_process['deposition_temperature']}")
        
        # 提取偏压
        bias_match = re.search(r'偏压.*?(-?\d+)\s*V.*?(-?\d+)\s*V', optimization_content)
        if bias_match:
            new_process["bias_voltage"] = int(bias_match.group(2))
        
        # 提取N₂流量
        n2_match = re.search(r'N[₂2]流量.*?(\d+)\s*sccm.*?(\d+)\s*sccm', optimization_content)
        if n2_match:
            new_process["n2_flow"] = int(n2_match.group(2))
        
        # 提取气压
        pressure_match = re.search(r'气压.*?(\d+\.?\d*)\s*Pa.*?(\d+\.?\d*)\s*Pa', optimization_content)
        if pressure_match:
            new_process["deposition_pressure"] = float(pressure_match.group(2))
        
        logger.info(f"[参数提取] 完成，新成分: {new_composition}")
        
        return {
            "new_composition": new_composition,
            "new_process": new_process,
            "extraction_source": selected_type
        }
    
    def _safe_float(self, value) -> Optional[float]:
        """安全转换为浮点数"""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None


# 单例
_experiment_analysis_service = None


def get_experiment_analysis_service() -> ExperimentAnalysisService:
    """获取实验分析服务单例"""
    global _experiment_analysis_service
    if _experiment_analysis_service is None:
        _experiment_analysis_service = ExperimentAnalysisService()
    return _experiment_analysis_service
