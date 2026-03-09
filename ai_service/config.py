import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
COHERE_API_KEY = os.getenv("COHERE_API_KEY", "")
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY", "")
LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "false")
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "CheerCloud")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")

# LangSmith 链路追踪
if LANGCHAIN_TRACING_V2 == "true" and LANGSMITH_API_KEY:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = LANGSMITH_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = LANGCHAIN_PROJECT

# 意图标签
INTENT_LABELS = ["anxiety", "depression", "crisis", "daily"]

# 对话策略
STRATEGY_MAP = {
    "anxiety":    "listening",           # 倾听型
    "depression": "guiding",             # 引导型
    "crisis":     "crisis_intervention", # 危机干预型
    "daily":      "listening",           # 日常倾诉 → 倾听型
}

# 危机关键词
CRISIS_KEYWORDS = [
    "suicide", "kill myself", "end my life", "want to die",
    "can't go on", "no reason to live", "hurt myself",
    "自杀", "不想活", "结束生命", "活不下去", "去死", "伤害自己"
]
