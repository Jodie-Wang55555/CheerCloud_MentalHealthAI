"""
Cohere 精排服务
- Self-RAG：对置信度不足的召回结果触发二次检索
- Cohere Rerank：语义感知精细化重排序
"""
from typing import List, Dict
import cohere

from config import COHERE_API_KEY


_cohere_client = cohere.Client(api_key=COHERE_API_KEY)

CONFIDENCE_THRESHOLD = 0.3  # RRF score 低于此值触发二次检索


# ── Cohere Rerank ────────────────────────────────────────
def cohere_rerank(query: str, documents: List[str], top_k: int = 5) -> List[Dict]:
    """
    使用 Cohere rerank-english-v3.0 对文档进行语义精排。
    返回: [{"text": str, "relevance_score": float, "rank": int}]
    """
    if not documents or not COHERE_API_KEY:
        # 无 API Key 时降级：直接返回原始顺序
        return [
            {"text": doc, "relevance_score": 1.0 - i * 0.1, "rank": i + 1}
            for i, doc in enumerate(documents[:top_k])
        ]

    try:
        response = _cohere_client.rerank(
            model="rerank-english-v3.0",
            query=query,
            documents=documents,
            top_n=min(top_k, len(documents)),
        )

        results = []
        for item in response.results:
            results.append({
                "text": documents[item.index],
                "relevance_score": item.relevance_score,
                "rank": len(results) + 1,
            })
        return results

    except Exception as e:
        print(f"[Reranker] Cohere rerank error: {e}, falling back to original order")
        return [
            {"text": doc, "relevance_score": 1.0 - i * 0.1, "rank": i + 1}
            for i, doc in enumerate(documents[:top_k])
        ]


# ── Self-RAG 置信度检查 ───────────────────────────────────
def needs_second_retrieval(fused_results: List[Dict]) -> bool:
    """
    Self-RAG：检查融合结果置信度，判断是否需要二次检索。
    若 top 结果的 RRF score 低于阈值，触发二次检索。
    """
    if not fused_results:
        return True
    top_score = fused_results[0].get("rrf_score", 0)
    return top_score < CONFIDENCE_THRESHOLD


# ── 精排主入口 ───────────────────────────────────────────
def rerank_results(
    query: str,
    fused_results: List[Dict],
    top_k: int = 5,
) -> List[Dict]:
    """
    对 RRF 融合结果进行 Cohere 语义精排。
    返回最终注入 LLM 的上下文列表。
    """
    if not fused_results:
        return []

    documents = [r["text"] for r in fused_results]
    reranked = cohere_rerank(query, documents, top_k=top_k)

    return reranked
