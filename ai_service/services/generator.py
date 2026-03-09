"""
个性化生成服务
- Chain-of-Thought Prompt：先推理用户情绪状态与深层需求，再生成回复
- 危机检测：高风险语义触发专属响应流程
- Citation 机制：回复关联用户历史表达，确保可追溯
- 三种对话策略：倾听型 / 引导型 / 危机干预型
"""
from typing import List, Dict, Tuple

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage

from config import GEMINI_API_KEY, CRISIS_KEYWORDS, STRATEGY_MAP
from models.schemas import Message


_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=GEMINI_API_KEY,
    temperature=0.7,
)


# ── 危机检测 ─────────────────────────────────────────────
def detect_crisis(message: str) -> bool:
    """关键词匹配 + 语义判断：检测高风险心理危机信号。"""
    msg_lower = message.lower()
    return any(kw in msg_lower for kw in CRISIS_KEYWORDS)


# ── 策略 Prompt 模板 ─────────────────────────────────────
def _get_strategy_prompt(strategy: str) -> str:
    prompts = {
        "listening": """You are a warm, empathetic mental health companion using a LISTENING strategy.
Your goal: Make the user feel truly heard and validated.
- Reflect back their feelings with empathy
- Ask one gentle follow-up question to encourage sharing
- Avoid giving direct advice unless asked
- Use phrases like "That sounds really hard", "I hear you", "It makes sense you feel this way" """,

        "guiding": """You are a compassionate mental health companion using a GUIDING strategy.
Your goal: Help the user find small, actionable steps forward.
- Acknowledge their pain first before suggesting anything
- Offer 1-2 gentle, concrete suggestions
- Frame suggestions as options, not prescriptions
- End with encouragement: "You've got this", "One step at a time" """,

        "crisis_intervention": """You are a mental health crisis support specialist.
This user may be in serious distress. Follow these steps STRICTLY:
1. IMMEDIATELY validate their pain: "I hear you. What you're feeling is real and serious."
2. Express genuine care: "I'm really glad you're talking to me right now."
3. Gently encourage professional help: "Please consider reaching out to a crisis line or trusted person."
4. Provide a crisis resource: In the US: 988 Suicide & Crisis Lifeline (call/text 988). In China: 北京心理危机研究与干预中心 010-82951332
5. Stay calm, do NOT minimize their feelings.""",
    }
    return prompts.get(strategy, prompts["listening"])


# ── CoT 个性化生成 ────────────────────────────────────────
async def generate_response(
    message: str,
    intent: str,
    strategy: str,
    context: List[Dict],
    history: List[Message],
) -> Tuple[str, List[str]]:
    """
    Chain-of-Thought 个性化生成：
    Step 1: 推理用户当前情绪状态与深层需求
    Step 2: 基于推理 + 历史上下文生成情感连贯的专业回复
    返回: (answer, citations)
    """
    # 构建历史上下文
    history_text = "\n".join(
        [f"{m.role.upper()}: {m.text}" for m in history[-6:]]
    ) if history else ""

    # 构建检索上下文 + Citation
    citations = []
    context_text = ""
    if context:
        context_text = "\n\n[User's Emotional History - use to personalize response]:\n"
        for i, item in enumerate(context[:3]):
            context_text += f"[{i+1}] {item['text']}\n"
            citations.append(item["text"][:100] + "...")

    # 策略系统提示
    strategy_prompt = _get_strategy_prompt(strategy)

    # Chain-of-Thought 完整提示
    cot_system = f"""{strategy_prompt}

IMPORTANT - Follow this Chain-of-Thought approach:
<reasoning>
First, silently reason:
1. What is the user's core emotional state right now?
2. What is their deeper underlying need? (to be heard / to find hope / to feel safe / etc.)
3. How does their emotional history (if available) inform my response?
4. What response approach fits the {strategy} strategy best?
</reasoning>

Then write your actual response. Do NOT include the <reasoning> tags in your output.

Response constraints:
- Maximum 4 sentences or 400 characters
- Warm, conversational tone
- No emojis - express warmth through words
- If referencing user's past experience, do so naturally (e.g., "Like when you mentioned feeling overwhelmed before...")
"""

    user_prompt = f"""Conversation history:
{history_text}
{context_text}
Current message: "{message}"
Intent detected: {intent}

Please respond as the supportive companion described above."""

    response = await _llm.ainvoke([
        SystemMessage(content=cot_system),
        HumanMessage(content=user_prompt),
    ])

    return response.content.strip(), citations


# ── 危机专属响应 ─────────────────────────────────────────
async def generate_crisis_response(message: str) -> str:
    """危机情况下的专属安全响应流程。"""
    response = await _llm.ainvoke([
        SystemMessage(content=_get_strategy_prompt("crisis_intervention")),
        HumanMessage(content=f'User said: "{message}". Respond with care and urgency.'),
    ])
    return response.content.strip()
