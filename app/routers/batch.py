"""批量评测路由"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..models import AnalyzeRequest, TaskResponse, TaskStatus, Dimension
from ..services.prompt_builder import build_prompt
from ..services.llm_client import call_llm
from ..services.evaluator import evaluate_task
from ..services.test_case_store import get_all_cases, get_cases_by_dimension
from ..config import settings


class BatchRequest(BaseModel):
    model: str | None = Field(None, description="指定模型")
    dimensions: list[str] | None = Field(None, description="指定维度（为空则全部）")


class BatchResultItem(BaseModel):
    task: TaskResponse
    evaluation: dict | None = None


class BatchResponse(BaseModel):
    model_used: str
    total_cases: int
    completed: int
    failed: int
    avg_score: float
    dimension_scores: dict[str, float]
    results: list[BatchResultItem]
    started_at: str
    finished_at: str


router = APIRouter(prefix="/api/v1/batch", tags=["batch"])


@router.post("/run", response_model=BatchResponse)
async def run_batch(req: BatchRequest):
    """批量运行所有测试用例，自动分析 + 评分"""
    model = req.model or settings.llm_model
    started_at = datetime.now(timezone.utc).isoformat()

    if req.dimensions:
        cases = []
        for d in req.dimensions:
            try:
                dim = Dimension(d)
                cases.extend(get_cases_by_dimension(dim))
            except ValueError:
                pass
    else:
        cases = get_all_cases()

    results: list[BatchResultItem] = []
    dim_scores: dict[str, list[float]] = {}
    completed = 0
    failed = 0

    for case in cases:
        analyze_req = AnalyzeRequest(
            code=case.code,
            language=case.language,
            dimension=case.dimension,
            input_data=case.input_data,
            target_language=case.target_language,
            model=model,
        )

        system_prompt, user_prompt = build_prompt(analyze_req)
        task = TaskResponse(
            dimension=case.dimension,
            code=case.code,
            language=case.language,
            model_used=model,
            prompt_sent=user_prompt,
            status=TaskStatus.RUNNING,
        )

        evaluation = None
        try:
            response = await call_llm(system_prompt, user_prompt, model=model)
            task.model_response = response
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now(timezone.utc).isoformat()
            completed += 1

            evaluation = await evaluate_task(task)
            dim_key = case.dimension.value
            dim_scores.setdefault(dim_key, []).append(evaluation.score)
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            failed += 1

        results.append(BatchResultItem(task=task, evaluation=evaluation.model_dump() if evaluation else None))

    all_scores = [r.evaluation["score"] for r in results if r.evaluation]
    avg_score = sum(all_scores) / len(all_scores) if all_scores else 0.0
    dimension_avgs = {k: sum(v) / len(v) for k, v in dim_scores.items()}

    return BatchResponse(
        model_used=model,
        total_cases=len(cases),
        completed=completed,
        failed=failed,
        avg_score=round(avg_score, 2),
        dimension_scores={k: round(v, 2) for k, v in dimension_avgs.items()},
        results=results,
        started_at=started_at,
        finished_at=datetime.now(timezone.utc).isoformat(),
    )
