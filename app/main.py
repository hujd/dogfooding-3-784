"""代码理解与分析 - 评测后端 API 服务"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import analyze, test_cases, batch
from .config import settings

app = FastAPI(
    title="代码理解与分析 评测 API",
    description="评测大模型代码理解与分析能力的后端服务",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze.router)
app.include_router(test_cases.router)
app.include_router(batch.router)


@app.get("/health")
async def health():
    return {"status": "ok", "model": settings.llm_model}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=settings.debug)
