"""
用户输入理解与意图识别
- LangChain 上下文压缩
- 问题重写（模糊情感表达 → 结构化意图）
- 4类意图标签：anxiety / depression / crisis / daily
"""
import json
from typing import List, Tuple

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage

from config import GEMINI_API_KEY, INTENT_LABELS
from models.schemas import Message


_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=GEMINI_API_KEY,
    temperature=0.1,
)


# ── 问题重写 ─────────────────────────────────────────────
async def rewrite_question(message: str, history: List[Message]) -> str:
    """
    将模糊情感表达结合历史上下文，重写为语义清晰的独立问题。
    例：'I don't know...' → 'User feels lost and overwhelmed, seeking direction and support'
    """
    if not history:
        return message

    history_text = "\n".join(
        [f"{m.role.upper()}: {m.text}" for m in history[-6:]]  # 最近6轮
    )

    prompt = f"""Given this conversation history:
{history_text}

And the user's latest message: "{message}"

Rewrite the user's message as a clear, standalone psychological support query 
that captures the full emotional context. Keep it concise (1-2 sentences).
Return ONLY the rewritten query, nothing else."""

    response = await _llm.ainvoke([HumanMessage(content=prompt)])
    return response.content.strip()


# ── 意图识别 ─────────────────────────────────────────────
async def classify_intent(message: str, history: List[Message]) -> Tuple[str, float]:
    """
    识别用户心理咨询意图标签。
    返回: (intent_label, confidence)
    """
    history_text = "\n".join(
        [f"{m.role.upper()}: {m.text}" for m in history[-4:]]
    ) if history else "No history"

    system_prompt = """You are a mental health intent classifier.
Classify the user's message into ONE of these categories:
- anxiety: worry, nervousness, panic, stress about future events
- depression: sadness, hopelessness, low energy, feeling empty
- crisis: self-harm thoughts, suicidal ideation, extreme distress
- daily: general emotional check-in, sharing daily feelings, seeking encouragement

Return a JSON object: {"intent": "<label>", "confidence": <0.0-1.0>, "reason": "<brief reason>"}
Return ONLY valid JSON."""

    user_prompt = f"""Conversation history:
{history_text}

Current message: "{message}"
"""

    response = await _llm.ainvoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ])

    try:
        content = response.content.strip()
        # 处理 Gemini 返回 markdown 代码块的情况 (```json ... ```)
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        result = json.loads(content)
        intent = result.get("intent", "daily")
        confidence = float(result.get("confidence", 0.7))
        if intent not in INTENT_LABELS:
            intent = "daily"
    except (json.JSONDecodeError, ValueError):
        # 最后兜底：直接从文本中查找意图标签
        content_lower = response.content.lower()
        intent = "daily"
        for label in INTENT_LABELS:
            if f'"intent": "{label}"' in content_lower or f"intent: {label}" in content_lower:
                intent = label
                break
        confidence = 0.6

    return intent, confidence


# ── 组合：理解用户输入 ────────────────────────────────────
async def understand_input(message: str, history: List[Message]) -> dict:
    """
    组合调用：问题重写 + 意图识别
    返回完整的输入理解结果
    """
    rewritten = await rewrite_question(message, history)
    intent, confidence = await classify_intent(rewritten, history)

    return {
        "original": message,
        "rewritten": rewritten,
        "intent": intent,
        "confidence": confidence,
    }
