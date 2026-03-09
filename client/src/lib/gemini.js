/**
 * CheerCloud AI - RAG 版本
 * 调用链路: 前端 → Express → Python FastAPI → Gemini + ChromaDB + Cohere
 */

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:3000";

console.log("🚀 CheerCloud RAG AI Initialized");

/**
 * 主对话接口 - 完整 RAG 流程
 * @param {string} userMessage
 * @param {Array}  history       [{ role, text }]
 * @returns {Promise<{answer, intent, strategy, is_crisis, citations}>}
 */
export async function callCheerCloudAI(userMessage, history = []) {
  try {
    console.log("📤 Sending to RAG pipeline:", userMessage);

    const response = await fetch(`${API_URL}/api/ai/chat`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: userMessage,
        history: history.map((m) => ({ role: m.role, text: m.parts?.[0]?.text || m.text || "" })),
      }),
    });

    if (!response.ok) {
      const err = await response.text();
      throw new Error(`AI service error: ${err}`);
    }

    const data = await response.json();
    console.log("✅ RAG Response:", data.intent, "|", data.strategy);
    return data.answer;

  } catch (error) {
    console.error("❌ AI Call Failed:", error);
    throw error;
  }
}

/**
 * 对话结束后保存情绪知识库
 * 在每次 chat session 结束时调用
 * @param {Array} conversation [{ role, text }]
 */
export async function saveEmotionMemory(conversation) {
  try {
    await fetch(`${API_URL}/api/ai/emotion`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ conversation }),
    });
    console.log("💾 Emotion memory saved");
  } catch (error) {
    console.warn("⚠️ Failed to save emotion memory:", error.message);
  }
}

// 保持向后兼容
export const prompt = `You are a compassionate mental health AI companion powered by RAG.`;
