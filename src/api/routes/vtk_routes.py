"""
VTK文件服务路由 - 提供VTK文件下载和访问
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pathlib import Path
from typing import Optional
import os
import re
from loguru import logger

# 创建路由
router = APIRouter(prefix="/api/vtk", tags=["VTK文件服务"])

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


@router.get("/file-info")
async def get_vtk_file_info(filepath: str):
    """
    获取VTK文件信息（不下载文件内容）
    
    Args:
        filepath: VTK文件路径（query参数，例如: ?filepath=conc-0.vtk 或 ?filepath=涂层-调幅分解/conc-0.vtk）
    
    Returns:
        VTK文件元数据
    """
    try:
        # 安全检查
        if not filepath.endswith('.vtk'):
            raise HTTPException(status_code=400, detail="只支持VTK文件格式")
        
        # 构建文件路径
        file_path = PROJECT_ROOT / filepath
        
        # 检查文件是否存在
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"文件不存在: {filepath}")
        
        # 读取文件头部信息
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = []
            for i, line in enumerate(f):
                lines.append(line.strip())
                if i >= 15:  # 只读取前16行
                    break
        
        # 解析头部信息
        metadata = _parse_vtk_header(lines)
        
        # 基本文件信息
        file_info = {
            "name": filepath,
            "size": file_path.stat().st_size,
            "size_mb": round(file_path.stat().st_size / 1024 / 1024, 2),
            "metadata": metadata
        }
        
        return file_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取VTK文件信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files/{filename:path}")
async def get_vtk_file(filename: str):
    """
    下载VTK文件（支持子文件夹）
    
    Args:
        filename: VTK文件路径（例如: conc-0.vtk 或 涂层-调幅分解/conc-0.vtk）
    
    Returns:
        VTK文件内容
    """
    try:
        # 安全检查：只允许访问.vtk文件
        if not filename.endswith('.vtk'):
            raise HTTPException(status_code=400, detail="只支持VTK文件格式")
        
        # 构建文件路径（从项目根目录）
        file_path = PROJECT_ROOT / filename
        
        # 检查文件是否存在
        if not file_path.exists():
            logger.warning(f"[VTK] 文件不存在: {file_path}")
            raise HTTPException(status_code=404, detail=f"文件不存在: {filename}")
        
        # 检查文件大小
        file_size = file_path.stat().st_size
        logger.info(f"[VTK] 请求文件: {filename}, 大小: {file_size / 1024 / 1024:.2f} MB")
        
        # 获取文件名（不含路径）
        file_basename = Path(filename).name
        
        # 返回文件响应
        return FileResponse(
            path=str(file_path),
            media_type="application/octet-stream",
            filename=file_basename,
            headers={
                "Content-Disposition": f'attachment; filename="{file_basename}"',
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[VTK] 获取文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取文件失败: {str(e)}")


def _parse_vtk_header(lines: list) -> dict:
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


@router.get("/list")
async def list_vtk_files():
    """
    列出所有可用的VTK文件
    
    Returns:
        List[dict]: VTK文件信息列表
    """
    try:
        vtk_files = []
        
        # 扫描项目根目录下的VTK文件
        for vtk_file in PROJECT_ROOT.glob("*.vtk"):
            file_info = {
                "name": vtk_file.name,
                "size": vtk_file.stat().st_size,
                "modified": vtk_file.stat().st_mtime
            }
            
            # 尝试解析VTK头部信息
            try:
                with open(vtk_file, 'r', encoding='utf-8', errors='ignore') as f:
                    header_lines = [f.readline() for _ in range(20)]
                    metadata = _parse_vtk_header(header_lines)
                    file_info.update(metadata)
            except Exception as e:
                logger.warning(f"无法解析VTK文件 {vtk_file.name}: {e}")
            
            vtk_files.append(file_info)
        
        return {
            "total": len(vtk_files),
            "files": vtk_files
        }
    
    except Exception as e:
        logger.error(f"列出VTK文件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/timeseries/{folder_name:path}")
async def get_timeseries_files(folder_name: str):
    """
    获取指定文件夹的时间序列VTK文件列表
    
    Args:
        folder_name: 文件夹名称（例如: 涂层-调幅分解）
        
    Returns:
        dict: 时间序列信息
    """
    try:
        folder_path = PROJECT_ROOT / folder_name
        
        if not folder_path.exists():
            raise HTTPException(status_code=404, detail=f"文件夹不存在: {folder_name}")
        
        if not folder_path.is_dir():
            raise HTTPException(status_code=400, detail=f"不是文件夹: {folder_name}")
        
        files = []
        
        # 扫描文件夹中的VTK文件
        for vtk_file in sorted(folder_path.glob("*.vtk")):
            # 从文件名提取时间步 (例如: conc-100.vtk -> 100)
            match = re.search(r'conc-(\d+)\.vtk', vtk_file.name)
            time_step = int(match.group(1)) if match else 0
            
            file_info = {
                "name": f"{folder_name}/{vtk_file.name}",  # 包含文件夹路径
                "fileName": vtk_file.name,  # 仅文件名
                "timeStep": time_step,
                "size": vtk_file.stat().st_size
            }
            
            files.append(file_info)
        
        # 按时间步排序
        files.sort(key=lambda x: x['timeStep'])
        
        # 提取时间步列表
        time_steps = [f['timeStep'] for f in files]
        
        return {
            "folder": folder_name,
            "total": len(files),
            "timeSteps": time_steps,
            "minTimeStep": min(time_steps) if time_steps else 0,
            "maxTimeStep": max(time_steps) if time_steps else 0,
            "files": files
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取时间序列文件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
