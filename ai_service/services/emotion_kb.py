"""
情绪知识库服务
- 每轮对话结束后提取情绪摘要
- 使用 Ollama nomic-embed-text 本地向量化
- 多粒度存储于 ChromaDB（摘要、情绪标签、用户偏好）
"""
import json
from datetime import datetime
from typing import List

import chromadb
from langchain_ollama import OllamaEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage

from config import GEMINI_API_KEY, OLLAMA_BASE_URL, CHROMA_PERSIST_DIR
from models.schemas import Message


# ── 初始化 ──────────────────────────────────────────────
_chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)

_embeddings = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url=OLLAMA_BASE_URL,
)

_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=GEMINI_API_KEY,
    temperature=0.3,
)


def _get_collection(user_id: str):
    """每个用户独立一个 ChromaDB collection，数据本地化。"""
    return _chroma_client.get_or_create_collection(
        name=f"user_{user_id}",
        metadata={"hnsw:space": "cosine"},
    )


# ── 情绪摘要提取 ─────────────────────────────────────────
async def extract_emotion_summary(conversation: List[Message]) -> dict:
    """
    使用 Gemini 对对话进行情绪摘要提取与关键事件标注。
    返回: { summary, emotion_label, key_events, user_preference }
    """
    conv_text = "\n".join(
        [f"{m.role.upper()}: {m.text}" for m in conversation]
    )

    system_prompt = """You are an expert psychological analyst.
Analyze the conversation and return a JSON object with:
- "summary": 2-3 sentence summary of user's emotional state (in the conversation's language)
- "emotion_label": one of [anxiety, depression, crisis, daily, stress, loneliness, grief]
- "key_events": list of up to 3 key emotional triggers or events mentioned
- "user_preference": what communication style the user responds well to

Return ONLY valid JSON, no markdown, no explanation."""

    response = await _llm.ainvoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Conversation:\n{conv_text}"),
    ])

    try:
        result = json.loads(response.content)
    except json.JSONDecodeError:
        # 容错处理
        result = {
            "summary": response.content[:300],
            "emotion_label": "daily",
            "key_events": [],
            "user_preference": "warm and supportive",
        }
    return result


# ── 存储到知识库 ─────────────────────────────────────────
async def save_to_knowledge_base(user_id: str, conversation: List[Message]) -> str:
    """
    提取情绪摘要并多粒度存入 ChromaDB。
    Multi-representation: 摘要、情绪标签、用户偏好分别向量化。
    """
    summary_data = await extract_emotion_summary(conversation)
    collection = _get_collection(user_id)
    timestamp = datetime.utcnow().isoformat()
    base_id = f"{user_id}_{timestamp}"

    # 三种粒度的文本
    representations = [
        {
            "id": f"{base_id}_summary",
            "text": summary_data["summary"],
            "type": "summary",
        },
        {
            "id": f"{base_id}_emotion",
            "text": f"Emotion: {summary_data['emotion_label']}. "
                    f"Key events: {', '.join(summary_data.get('key_events', []))}",
            "type": "emotion",
        },
        {
            "id": f"{base_id}_preference",
            "text": f"User preference: {summary_data.get('user_preference', '')}",
            "type": "preference",
        },
    ]

    for rep in representations:
        embedding = _embeddings.embed_query(rep["text"])
        collection.add(
            ids=[rep["id"]],
            embeddings=[embedding],
            documents=[rep["text"]],
            metadatas=[{
                "user_id": user_id,
                "type": rep["type"],
                "emotion_label": summary_data["emotion_label"],
                "timestamp": timestamp,
            }],
        )

    return summary_data["summary"]


# ── 从知识库检索 ─────────────────────────────────────────
def query_knowledge_base(user_id: str, query: str, top_k: int = 5) -> List[dict]:
    """
    向量检索用户个人情绪知识库，返回最相关的历史情绪片段。
    """
    try:
        collection = _get_collection(user_id)
        if collection.count() == 0:
            return []

        query_embedding = _embeddings.embed_query(query)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        records = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            records.append({
                "text": doc,
                "metadata": meta,
                "score": 1 - dist,  # cosine distance → similarity
            })
        return records

    except Exception as e:
        print(f"[EmotionKB] query error: {e}")
        return []
