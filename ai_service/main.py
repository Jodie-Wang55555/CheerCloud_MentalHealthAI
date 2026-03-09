"""
CheerCloud AI Service - FastAPI 入口
端口: 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.chat import router as chat_router

app = FastAPI(
    title="CheerCloud AI Service",
    description="心理健康 RAG AI 服务 - Gemini + ChromaDB + Cohere",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)


@app.get("/")
async def root():
    return {
        "service": "CheerCloud AI",
        "version": "2.0.0",
        "stack": ["Gemini 2.5 Flash", "ChromaDB", "Ollama", "Cohere", "LangChain"],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
