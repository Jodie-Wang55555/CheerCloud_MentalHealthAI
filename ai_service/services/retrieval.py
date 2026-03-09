"""
混合检索服务
- BM25 关键词检索
- ChromaDB 向量语义检索
- RRF (Reciprocal Rank Fusion) 融合排序
- Adaptive 路由：根据意图动态调整检索策略
"""
from typing import List, Dict
from rank_bm25 import BM25Okapi

from config import STRATEGY_MAP
from services.emotion_kb import query_knowledge_base


# ── BM25 检索 ────────────────────────────────────────────
def bm25_search(documents: List[str], query: str, top_k: int = 5) -> List[Dict]:
    """
    对文档列表进行 BM25 关键词检索。
    返回: [{"text": str, "score": float, "rank": int}]
    """
    if not documents:
        return []

    tokenized_docs = [doc.lower().split() for doc in documents]
    tokenized_query = query.lower().split()

    bm25 = BM25Okapi(tokenized_docs)
    scores = bm25.get_scores(tokenized_query)

    ranked = sorted(
        enumerate(scores), key=lambda x: x[1], reverse=True
    )[:top_k]

    return [
        {"text": documents[i], "score": float(s), "rank": rank + 1}
        for rank, (i, s) in enumerate(ranked)
        if s > 0
    ]


# ── RRF 融合 ─────────────────────────────────────────────
def rrf_fusion(
    bm25_results: List[Dict],
    vector_results: List[Dict],
    k: int = 60,
) -> List[Dict]:
    """
    Reciprocal Rank Fusion：融合 BM25 和向量检索结果。
    RRF score = Σ 1/(k + rank_i)
    """
    scores: Dict[str, float] = {}
    texts: Dict[str, str] = {}

    for rank, item in enumerate(bm25_results, start=1):
        key = item["text"]
        texts[key] = key
        scores[key] = scores.get(key, 0) + 1 / (k + rank)

    for rank, item in enumerate(vector_results, start=1):
        key = item["text"]
        texts[key] = key
        scores[key] = scores.get(key, 0) + 1 / (k + rank)

    fused = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    return [
        {"text": text, "rrf_score": score, "rank": i + 1}
        for i, (text, score) in enumerate(fused)
    ]


# ── Adaptive 路由 ────────────────────────────────────────
def get_retrieval_config(intent: str) -> Dict:
    """
    根据意图标签动态配置检索策略：
    - crisis: 优先检索危机干预相关历史，top_k 更多
    - anxiety/depression: 平衡 BM25 和向量
    - daily: 轻量检索
    """
    configs = {
        "crisis": {
            "top_k": 8,
            "bm25_weight": 0.4,
            "vector_weight": 0.6,
            "strategy": "crisis_intervention",
        },
        "anxiety": {
            "top_k": 5,
            "bm25_weight": 0.5,
            "vector_weight": 0.5,
            "strategy": "listening",
        },
        "depression": {
            "top_k": 6,
            "bm25_weight": 0.4,
            "vector_weight": 0.6,
            "strategy": "guiding",
        },
        "daily": {
            "top_k": 3,
            "bm25_weight": 0.5,
            "vector_weight": 0.5,
            "strategy": "listening",
        },
    }
    return configs.get(intent, configs["daily"])


# ── 混合检索主入口 ────────────────────────────────────────
def hybrid_search(
    user_id: str,
    query: str,
    intent: str,
    top_k: int = None,
) -> List[Dict]:
    """
    自适应混合检索：
    1. 从 ChromaDB 向量检索用户情绪知识库
    2. 对检索结果做 BM25 精确匹配
    3. RRF 融合两路结果
    返回去重融合后的上下文片段列表
    """
    config = get_retrieval_config(intent)
    k = top_k or config["top_k"]

    # 1. 向量检索（从 ChromaDB 个人情绪库）
    vector_results = query_knowledge_base(user_id, query, top_k=k * 2)
    if not vector_results:
        return []

    # 2. BM25 检索（在向量结果上做精确匹配）
    documents = [r["text"] for r in vector_results]
    bm25_results = bm25_search(documents, query, top_k=k)

    # 3. RRF 融合
    fused = rrf_fusion(bm25_results, vector_results[:k])

    return fused[:k]
