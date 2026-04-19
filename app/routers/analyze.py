"""代码分析路由"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from ..models import AnalyzeRequest, EvaluateRequest, TaskResponse, TaskStatus, EvaluationResult
from ..services.prompt_builder import build_prompt
from ..services.llm_client import call_llm
from ..services.evaluator import evaluate_task
from ..config import settings

router = APIRouter(prefix="/api/v1", tags=["analyze"])

_tasks: dict[str, TaskResponse] = {}
_evaluations: dict[str, EvaluationResult] = {}


@router.post("/analyze", response_model=TaskResponse)
async def create_analysis(req: AnalyzeRequest):
    """提交代码分析任务"""
    system_prompt, user_prompt = build_prompt(req)
    model = req.model or settings.llm_model

    task = TaskResponse(
        dimension=req.dimension,
        code=req.code,
        language=req.language,
        model_used=model,
        prompt_sent=user_prompt,
        status=TaskStatus.RUNNING,
    )

    try:
        response = await call_llm(system_prompt, user_prompt, model=model)
        task.model_response = response
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now(timezone.utc).isoformat()
    except Exception as e:
        task.status = TaskStatus.FAILED
        task.error = str(e)

    _tasks[task.task_id] = task
    return task


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """查询任务结果"""
    task = _tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


@router.get("/tasks", response_model=list[TaskResponse])
async def list_tasks(dimension: str | None = None, status: str | None = None, limit: int = 50):
    """列出所有任务"""
    results = list(_tasks.values())
    if dimension:
        results = [t for t in results if t.dimension.value == dimension]
    if status:
        results = [t for t in results if t.status.value == status]
    return results[-limit:]


@router.post("/evaluate", response_model=EvaluationResult)
async def evaluate(req: EvaluateRequest):
    """对模型返回结果进行评分"""
    task = _tasks.get(req.task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {req.task_id} not found")
    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail=f"Task not completed")

    result = await evaluate_task(task, req.reference_answer)
    _evaluations[req.task_id] = result
    return result


@router.get("/evaluations/{task_id}", response_model=EvaluationResult)
async def get_evaluation(task_id: str):
    """查询评分结果"""
    ev = _evaluations.get(task_id)
    if not ev:
        raise HTTPException(status_code=404, detail=f"Evaluation not found")
    return ev
