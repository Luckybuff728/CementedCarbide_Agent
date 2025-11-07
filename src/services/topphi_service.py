"""
TopPhi模拟服务 - 第一性原理沉积过程结构预测
"""
from typing import Dict, Any, Optional
import logging
import time
import os
from pathlib import Path
import base64

logger = logging.getLogger(__name__)


class TopPhiService:
    """TopPhi模拟服务 - 沉积过程结构预测"""
    
    def __init__(self):
        self.simulation_cache = {}  # TODO: 实现缓存机制
        # VTK文件路径配置
        self.project_root = Path(__file__).parent.parent.parent
        self.mock_vtk_file = self.project_root / "conc-0.vtk"
    
    def simulate_deposition(self, composition: Dict, params: Dict) -> Dict[str, Any]:
        """
        TopPhi模拟 - 预测沉积结构
        
        Args:
            composition: 涂层成分 {"al_content": float, "ti_content": float, "n_content": float}
            params: 工艺参数 {"deposition_temperature": float, "bias_voltage": float, ...}
        
        Returns:
            TopPhi模拟结果
        """
        logger.info(f"[TopPhi模拟] 开始 - Al={composition.get('al_content')}%, Ti={composition.get('ti_content')}%")
        
        # 模拟计算时间
        time.sleep(3)
        
        # 检查是否有时间序列数据
        timeseries_folder = self.project_root / "涂层-调幅分解"
        has_timeseries = timeseries_folder.exists() and timeseries_folder.is_dir()
        
        if has_timeseries:
            # 返回时间序列标记
            vtk_data = {
                "type": "timeseries",
                "folder": "涂层-调幅分解",
                "description": "相场模拟时间序列数据"
            }
        else:
            # 读取单个VTK文件
            vtk_data = self._read_vtk_file(self.mock_vtk_file)
            vtk_data["type"] = "single"
        
        topphi_result = {
            "grain_size_nm": self._predict_grain_size(composition, params),
            "preferred_orientation": self._predict_orientation(composition),
            "residual_stress_gpa": self._predict_stress(params),
            "lattice_constant": 4.15,
            "formation_energy": -0.85,
            "confidence": 0.82,
            "simulation_time": 120,
            # VTK可视化数据
            "vtk_data": vtk_data
        }
        
        logger.info(f"[TopPhi模拟] 完成 - 晶粒尺寸: {topphi_result['grain_size_nm']} nm")
        logger.info(f"[TopPhi模拟] VTK数据已加载 - {vtk_data.get('dimensions')}")
        
        return topphi_result
    
    def _predict_grain_size(self, composition: Dict, params: Dict) -> float:
        """预测晶粒尺寸（简化模型）"""
        # 基础晶粒尺寸
        base_size = 10.0
        
        # Al含量影响（Al含量越高，晶粒越细）
        al_factor = 1.0 - (composition.get('al_content', 0) / 100) * 0.3
        
        # 温度影响（温度越高，晶粒越大）
        temp = params.get('deposition_temperature', 500)
        temp_factor = 1.0 + (temp - 500) / 1000
        
        return round(base_size * al_factor * temp_factor, 1)
    
    def _predict_orientation(self, composition: Dict) -> str:
        """预测择优取向"""
        al_content = composition.get('al_content', 0)
        
        if al_content > 50:
            return "(111)"
        elif al_content > 30:
            return "(200)"
        else:
            return "(220)"
    
    def _predict_stress(self, params: Dict) -> float:
        """预测残余应力"""
        # 基础应力
        base_stress = -2.0
        
        # 偏压影响
        bias = params.get('bias_voltage', 0)
        bias_factor = 1.0 + (bias - 100) / 200
        
        return round(base_stress * bias_factor, 2)
    
    def _read_vtk_file(self, vtk_file_path: Path) -> Dict[str, Any]:
        """
        读取VTK文件并解析为结构化数据
        
        Args:
            vtk_file_path: VTK文件路径
        
        Returns:
            包含VTK数据的字典
        """
        try:
            if not vtk_file_path.exists():
                logger.warning(f"[VTK] 文件不存在: {vtk_file_path}")
                return self._get_empty_vtk_data()
            
            logger.info(f"[VTK] 读取文件: {vtk_file_path}")
            
            # 读取VTK文件头部信息
            with open(vtk_file_path, 'r', encoding='utf-8') as f:
                lines = []
                for i, line in enumerate(f):
                    lines.append(line.strip())
                    if i >= 15:  # 读取前16行获取元数据
                        break
            
            # 解析VTK头部
            vtk_metadata = self._parse_vtk_header(lines)
            
            # 读取文件大小
            file_size = vtk_file_path.stat().st_size
            
            # 对于大文件，只读取部分数据用于预览
            # 完整数据可以通过文件路径由前端按需加载
            vtk_result = {
                "file_path": str(vtk_file_path),
                "file_name": vtk_file_path.name,
                "file_size": file_size,
                "file_size_mb": round(file_size / 1024 / 1024, 2),
                "metadata": vtk_metadata,
                "dimensions": vtk_metadata.get("dimensions"),
                "point_count": vtk_metadata.get("point_count"),
                "data_type": vtk_metadata.get("data_type"),
                "scalar_name": vtk_metadata.get("scalar_name"),
                # 提供相对路径供前端访问
                "relative_path": vtk_file_path.name
            }
            
            logger.info(f"[VTK] 解析完成 - 维度: {vtk_metadata.get('dimensions')}, 点数: {vtk_metadata.get('point_count')}")
            
            return vtk_result
            
        except Exception as e:
            logger.error(f"[VTK] 读取失败: {e}")
            return self._get_empty_vtk_data()
    
    def _parse_vtk_header(self, lines: list) -> Dict[str, Any]:
        """
        解析VTK文件头部信息
        
        Args:
            lines: VTK文件的前几行
        
        Returns:
            解析后的元数据字典
        """
        metadata = {}
        
        try:
            # 第1行: 版本信息
            if len(lines) > 0:
                metadata["version"] = lines[0].replace("# vtk DataFile Version ", "").strip()
            
            # 第2行: 描述信息
            if len(lines) > 1:
                metadata["description"] = lines[1].strip()
            
            # 第3行: 数据格式
            if len(lines) > 2:
                metadata["format"] = lines[2].strip()
            
            # 第4行: 数据集类型
            if len(lines) > 3:
                metadata["dataset_type"] = lines[3].replace("DATASET ", "").strip()
            
            # 第5行: 维度信息
            if len(lines) > 4 and "DIMENSIONS" in lines[4]:
                dims = lines[4].replace("DIMENSIONS ", "").strip().split()
                metadata["dimensions"] = [int(d) for d in dims]
                metadata["dimensions_str"] = f"{dims[0]}×{dims[1]}×{dims[2]}"
            
            # 第6行: 纵横比
            if len(lines) > 5 and "ASPECT_RATIO" in lines[5]:
                metadata["aspect_ratio"] = lines[5].replace("ASPECT_RATIO ", "").strip()
            
            # 第7行: 原点
            if len(lines) > 6 and "ORIGIN" in lines[6]:
                metadata["origin"] = lines[6].replace("ORIGIN ", "").strip()
            
            # 第9行: 点数据数量
            if len(lines) > 8 and "POINT_DATA" in lines[8]:
                metadata["point_count"] = int(lines[8].replace("POINT_DATA ", "").strip())
            
            # 第10行: 标量类型
            if len(lines) > 9 and "SCALARS" in lines[9]:
                parts = lines[9].replace("SCALARS ", "").strip().split()
                metadata["scalar_name"] = parts[0] if len(parts) > 0 else "unknown"
                metadata["data_type"] = parts[1] if len(parts) > 1 else "unknown"
            
        except Exception as e:
            logger.warning(f"[VTK] 解析头部信息出错: {e}")
        
        return metadata
    
    def _get_empty_vtk_data(self) -> Dict[str, Any]:
        """返回空的VTK数据结构"""
        return {
            "file_path": None,
            "file_name": None,
            "file_size": 0,
            "file_size_mb": 0,
            "metadata": {},
            "dimensions": None,
            "point_count": 0,
            "data_type": None,
            "scalar_name": None,
            "relative_path": None
        }
