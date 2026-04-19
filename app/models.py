"""数据模型定义"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Dimension(str, Enum):
    """评测维度"""
    COMPREHENSION = "comprehension"
    BUG_DETECTION = "bug_detection"
    COMPLEXITY = "complexity"
    REFACTORING = "refactoring"
    SECURITY = "security"
    EXECUTION_TRACE = "execution_trace"
    TRANSLATION = "translation"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalyzeRequest(BaseModel):
    """提交代码分析任务"""
    code: str = Field(..., description="待分析的代码")
    language: str = Field("python", description="代码语言")
    dimension: Dimension = Field(..., description="分析维度")
    input_data: Optional[str] = Field(None, description="执行推演的输入数据")
    target_language: Optional[str] = Field(None, description="跨语言翻译的目标语言")
    model: Optional[str] = Field(None, description="指定使用的大模型")


class EvaluateRequest(BaseModel):
    """对模型返回结果进行评分"""
    task_id: str = Field(..., description="任务 ID")
    reference_answer: Optional[str] = Field(None, description="参考标准答案")


class TaskResponse(BaseModel):
    """任务结果"""
    task_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    dimension: Dimension
    status: TaskStatus = TaskStatus.PENDING
    code: str
    language: str
    model_used: str = ""
    prompt_sent: str = ""
    model_response: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    error: Optional[str] = None


class EvaluationResult(BaseModel):
    """评分结果"""
    task_id: str
    dimension: Dimension
    score: float = Field(..., ge=1.0, le=5.0)
    breakdown: dict = Field(default_factory=dict)
    issues: list[str] = Field(default_factory=list)
    issue_types: list[str] = Field(default_factory=list)
    summary: str = ""
    evaluated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class TestCase(BaseModel):
    """测试用例"""
    id: str
    dimension: Dimension
    title: str
    description: str
    code: str
    language: str
    expected_key_points: list[str] = Field(default_factory=list)
    known_bugs: list[str] = Field(default_factory=list)
    known_vulnerabilities: list[str] = Field(default_factory=list)
    expected_output: Optional[str] = None
    input_data: Optional[str] = None
    target_language: Optional[str] = None
    expected_complexity: Optional[str] = None
