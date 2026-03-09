"""
聊天 API 路由
- POST /api/ai/chat     主对话接口（完整 RAG 流程）
- POST /api/ai/emotion  对话结束后保存情绪知识库
- GET  /api/ai/health   服务健康检查
"""
from fastapi import APIRouter, HTTPException

from models.schemas import ChatRequest, ChatResponse, SaveEmotionRequest, SaveEmotionResponse
from services.intent import understand_input
from services.retrieval import hybrid_search
from services.reranker import rerank_results, needs_second_retrieval
from services.generator import generate_response, generate_crisis_response, detect_crisis
from services.emotion_kb import save_to_knowledge_base
from config import STRATEGY_MAP

router = APIRouter(prefix="/api/ai", tags=["AI"])


@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "CheerCloud AI"}


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    完整 RAG 对话流程：
    1. 危机检测（快速路径）
    2. 意图识别 + 问题重写
    3. Adaptive 混合检索（BM25 + Vector + RRF）
    4. Self-RAG 二次检索判断
    5. Cohere 精排
    6. CoT 个性化生成
    """
    try:
        # ── Step 1: 危机检测（快速路径）───────────────────
        is_crisis = detect_crisis(req.message)
        if is_crisis:
            crisis_answer = await generate_crisis_response(req.message)
            return ChatResponse(
                answer=crisis_answer,
                intent="crisis",
                strategy="crisis_intervention",
                retrieved_context=[],
                is_crisis=True,
                citations=[],
            )

        # ── Step 2: 意图识别 + 问题重写 ──────────────────
        understanding = await understand_input(req.message, req.history or [])
        intent = understanding["intent"]
        rewritten_query = understanding["rewritten"]
        strategy = STRATEGY_MAP.get(intent, "listening")

        # ── Step 3: 混合检索 ──────────────────────────────
        fused_results = hybrid_search(
            user_id=req.user_id,
            query=rewritten_query,
            intent=intent,
        )

        # ── Step 4: Self-RAG 二次检索 ────────────────────
        if needs_second_retrieval(fused_results):
            # 用原始消息再检索一次（不同视角）
            second_results = hybrid_search(
                user_id=req.user_id,
                query=req.message,
                intent=intent,
            )
            # 合并去重
            seen = {r["text"] for r in fused_results}
            for r in second_results:
                if r["text"] not in seen:
                    fused_results.append(r)
                    seen.add(r["text"])

        # ── Step 5: Cohere 精排 ───────────────────────────
        reranked = rerank_results(rewritten_query, fused_results, top_k=3)

        # ── Step 6: CoT 个性化生成 ────────────────────────
        answer, citations = await generate_response(
            message=req.message,
            intent=intent,
            strategy=strategy,
            context=reranked,
            history=req.history or [],
        )

        return ChatResponse(
            answer=answer,
            intent=intent,
            strategy=strategy,
            retrieved_context=[r["text"] for r in reranked],
            is_crisis=False,
            citations=citations,
        )

    except Exception as e:
        print(f"[Chat API] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/emotion", response_model=SaveEmotionResponse)
async def save_emotion(req: SaveEmotionRequest):
    """
    对话结束后调用：提取情绪摘要并存入个人情绪知识库。
    前端在每次对话会话结束时调用此接口。
    """
    try:
        if not req.conversation:
            return SaveEmotionResponse(success=False, summary="No conversation to save")

        summary = await save_to_knowledge_base(req.user_id, req.conversation)
        return SaveEmotionResponse(success=True, summary=summary)

    except Exception as e:
        print(f"[Emotion API] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
