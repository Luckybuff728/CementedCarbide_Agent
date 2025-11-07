"""
涂层相关API路由
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uuid
import logging
from datetime import datetime

from ...models.coating_models import CoatingInput
from ...graph.workflow_manager import workflow_manager

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/coating", tags=["coating"])


# API模型定义
class TaskCreateRequest(BaseModel):
    """任务创建请求"""
    coating_input: CoatingInput
    user_id: Optional[str] = None


class TaskUpdateRequest(BaseModel):
    """任务更新请求"""
    task_id: str
    action: str  # "select_optimization" | "add_results"
    data: Dict[str, Any]


class TaskResponse(BaseModel):
    """任务响应"""
    task_id: str
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None


@router.post("/submit", response_model=TaskResponse)
async def submit_coating_task(request: TaskCreateRequest):
    """
    提交涂层优化任务
    """
    try:
        # 生成任务ID
        task_id = f"TASK_{uuid.uuid4().hex[:8]}"
        thread_id = f"THREAD_{uuid.uuid4().hex[:8]}"
        
        # 准备输入数据
        input_data = {
            "composition": request.coating_input.composition.model_dump(),
            "process_params": request.coating_input.process_params.model_dump(),
            "structure_design": request.coating_input.structure_design.model_dump(),
            "target_requirements": request.coating_input.target_requirements.model_dump()
        }
        
        logger.info(f"提交新任务: {task_id}")
        
        return TaskResponse(
            task_id=task_id,
            status="created",
            message="任务已创建，请使用WebSocket连接获取实时处理结果",
            data={"thread_id": thread_id, "input_data": input_data}
        )
    
    except Exception as e:
        logger.error(f"提交任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/task/{task_id}", response_model=TaskResponse)
async def get_task_status(task_id: str):
    """
    获取任务状态
    """
    try:
        state = workflow_manager.get_task_state(task_id)
        return TaskResponse(
            task_id=task_id,
            status=state.get("workflow_status", "unknown"),
            message="获取任务状态成功",
            data={
                "current_step": state.get("current_step"),
                "predictions": state.get("performance_prediction"),
                "suggestions": state.get("optimization_suggestions")
            }
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="任务不存在")
    except Exception as e:
        logger.error(f"获取任务状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/task/{task_id}/update")
async def update_task(task_id: str, request: TaskUpdateRequest):
    """
    更新任务状态
    """
    try:
        if request.action == "select_optimization":
            workflow_manager.update_task_selection(task_id, request.data)
            return {"message": "优化方案选择已更新"}
        
        elif request.action == "add_experiment_results":
            workflow_manager.update_experiment_results(task_id, request.data)
            return {"message": "实验结果已添加"}
        
        else:
            raise HTTPException(status_code=400, detail="不支持的操作类型")
    
    except ValueError:
        raise HTTPException(status_code=404, detail="任务不存在")
    except Exception as e:
        logger.error(f"更新任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks")
async def list_active_tasks():
    """
    列出所有活动任务
    """
    try:
        tasks = workflow_manager.list_active_tasks()
        return {
            "active_tasks": tasks,
            "count": len(tasks)
        }
    except Exception as e:
        logger.error(f"列出任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
