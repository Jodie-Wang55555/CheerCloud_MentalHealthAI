"""
端到端评估脚本
- 自建评估集：覆盖 4 类意图
- 指标：意图识别准确率、对话轮次
- 对比基线（无画像注入）vs 完整 RAG 版本
"""
import asyncio
import json
from services.intent import classify_intent
from models.schemas import Message

# ── 自建评估集 ────────────────────────────────────────────
# 共 50 条，分两组：
# [Easy] 语义明显，基线也能答对
# [Hard] 模糊边界，基线易误判，测试 Prompt 工程的真实价值

EVAL_DATASET = [

    # ── EASY: anxiety（语义明显）──────────────────────────
    {"message": "I'm so anxious about my job interview tomorrow, I can't sleep", "label": "anxiety", "difficulty": "easy"},
    {"message": "I have a presentation next week and I can't stop panicking", "label": "anxiety", "difficulty": "easy"},
    {"message": "My heart keeps racing and I don't know why, I'm always worried", "label": "anxiety", "difficulty": "easy"},

    # ── HARD: anxiety（无明显焦虑词）─────────────────────
    {"message": "I keep replaying that conversation in my head over and over", "label": "anxiety", "difficulty": "hard"},
    {"message": "I don't know why but I just feel unsettled and I can't shake it", "label": "anxiety", "difficulty": "hard"},
    {"message": "I've been checking my phone constantly waiting to hear back, it's driving me crazy", "label": "anxiety", "difficulty": "hard"},
    {"message": "My mind keeps jumping to all the things that could go wrong", "label": "anxiety", "difficulty": "hard"},
    {"message": "I've been having trouble focusing lately, my thoughts just race", "label": "anxiety", "difficulty": "hard"},

    # ── EASY: depression（语义明显）──────────────────────
    {"message": "I feel empty and I don't know why. Nothing makes me happy anymore", "label": "depression", "difficulty": "easy"},
    {"message": "I feel so hopeless, like things will never get better", "label": "depression", "difficulty": "easy"},
    {"message": "I've lost interest in things I used to love", "label": "depression", "difficulty": "easy"},

    # ── HARD: depression（轻描淡写）──────────────────────
    {"message": "I've been sleeping a lot lately, I guess I'm just tired", "label": "depression", "difficulty": "hard"},
    {"message": "I don't really feel like doing much these days, everything takes so much effort", "label": "depression", "difficulty": "hard"},
    {"message": "Things have been pretty heavy lately and I can't really explain why", "label": "depression", "difficulty": "hard"},
    {"message": "I just feel kind of flat, like nothing really excites me anymore", "label": "depression", "difficulty": "hard"},
    {"message": "I've been canceling plans a lot lately, I just don't have the energy", "label": "depression", "difficulty": "hard"},
    {"message": "I feel really disconnected from everyone around me lately", "label": "depression", "difficulty": "hard"},

    # ── EASY: crisis（语义直接）──────────────────────────
    {"message": "I don't want to be here anymore", "label": "crisis", "difficulty": "easy"},
    {"message": "I've been thinking about ending it all", "label": "crisis", "difficulty": "easy"},

    # ── HARD: crisis（被动意念，语义隐晦）─────────────────
    {"message": "I'm just so tired of everything, I want it all to stop", "label": "crisis", "difficulty": "hard"},
    {"message": "I wonder if anyone would even notice if I just disappeared", "label": "crisis", "difficulty": "hard"},
    {"message": "Sometimes I think things would be a lot easier if I just wasn't around", "label": "crisis", "difficulty": "hard"},
    {"message": "I keep having these dark thoughts and I don't know how to make them stop", "label": "crisis", "difficulty": "hard"},
    {"message": "I feel like such a burden to everyone, they'd all be better off", "label": "crisis", "difficulty": "hard"},
    {"message": "I've been thinking a lot about what happens after we're gone", "label": "crisis", "difficulty": "hard"},

    # ── EASY: daily（语义明显）───────────────────────────
    {"message": "I just needed someone to talk to today", "label": "daily", "difficulty": "easy"},
    {"message": "Had a tough day at work but I'm okay", "label": "daily", "difficulty": "easy"},
    {"message": "Can you give me some encouragement?", "label": "daily", "difficulty": "easy"},

    # ── HARD: daily（看起来像负面情绪但其实只是日常）──────
    {"message": "I'm feeling a bit down but nothing serious, just one of those days", "label": "daily", "difficulty": "hard"},
    {"message": "Today was really hard and I just wanted to vent a little", "label": "daily", "difficulty": "hard"},
    {"message": "I've been a bit more emotional than usual lately, probably just stress", "label": "daily", "difficulty": "hard"},
    {"message": "I'm exhausted but I know it'll pass, just need to get through this week", "label": "daily", "difficulty": "hard"},
    {"message": "I feel a bit lost lately but I think I just need to figure some things out", "label": "daily", "difficulty": "hard"},
    {"message": "I cried today and I'm not totally sure why, but I feel a bit better now", "label": "daily", "difficulty": "hard"},

    # ── HARD: 跨类别边界（最难）──────────────────────────
    {"message": "My chest feels tight all the time and I can't eat properly", "label": "anxiety", "difficulty": "hard"},
    {"message": "I've been having really dark thoughts lately but I think I'm okay", "label": "crisis", "difficulty": "hard"},
    {"message": "I don't know if I'm depressed or just going through a rough patch", "label": "depression", "difficulty": "hard"},
    {"message": "I keep thinking there's no way out of this situation", "label": "crisis", "difficulty": "hard"},
    {"message": "Everything feels pointless but I'm still getting up and going to work", "label": "depression", "difficulty": "hard"},
    {"message": "I've been snapping at people I care about and I hate myself for it", "label": "anxiety", "difficulty": "hard"},
    {"message": "I just feel really numb, like I'm watching my life from outside", "label": "depression", "difficulty": "hard"},
    {"message": "I don't want to worry anyone but I haven't been feeling like myself", "label": "depression", "difficulty": "hard"},
    {"message": "Sometimes the only thing stopping me is thinking about my family", "label": "crisis", "difficulty": "hard"},
    {"message": "I feel like no matter what I do it's never enough, I'm always failing", "label": "anxiety", "difficulty": "hard"},
    {"message": "I've been isolating myself but I tell myself it's because I need rest", "label": "depression", "difficulty": "hard"},
    {"message": "I feel really low today but honestly it happens sometimes, it's fine", "label": "daily", "difficulty": "hard"},
    {"message": "Things are hard right now but I'm trying to stay positive", "label": "daily", "difficulty": "hard"},
    {"message": "I've been crying every night this week but I can't explain why", "label": "depression", "difficulty": "hard"},
    {"message": "I'm scared of my own thoughts lately", "label": "crisis", "difficulty": "hard"},
]


async def classify_intent_baseline(message: str) -> str:
    """
    基线版本：无任何 Prompt 工程，只用最简单的分类指令。
    模拟没有 RAG 增强时的原始模型能力。
    """
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain.schema import HumanMessage
    import os
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0.1,
    )
    prompt = f'Classify this message into one of: anxiety, depression, crisis, daily. Reply with just the label.\n\nMessage: "{message}"'
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    label = response.content.strip().lower()
    for l in ["anxiety", "depression", "crisis", "daily"]:
        if l in label:
            return l
    return "daily"


async def run_evaluation():
    """运行意图识别准确率评估。"""
    correct = 0
    results = []

    print("🔍 开始评估意图识别准确率...\n")

    for item in EVAL_DATASET:
        predicted_intent, confidence = await classify_intent(item["message"], [])
        is_correct = predicted_intent == item["label"]
        if is_correct:
            correct += 1

        results.append({
            "message": item["message"][:60] + "...",
            "expected": item["label"],
            "predicted": predicted_intent,
            "confidence": round(confidence, 2),
            "correct": is_correct,
        })

        status = "✅" if is_correct else "❌"
        print(f"{status} [{item['label']} → {predicted_intent}] ({confidence:.0%}) {item['message'][:50]}")

    easy_items  = [r for r in results if EVAL_DATASET[[i["message"] for i in EVAL_DATASET].index(r["message"][:60].rstrip("."))]["difficulty"] == "easy"] if False else []
    rag_accuracy       = correct / len(EVAL_DATASET)
    hard_results       = [r for r in results if not r.get("easy")]
    rag_hard_correct   = sum(1 for item, r in zip(EVAL_DATASET, results) if item["difficulty"] == "hard" and r["correct"])
    rag_easy_correct   = sum(1 for item, r in zip(EVAL_DATASET, results) if item["difficulty"] == "easy" and r["correct"])
    hard_total         = sum(1 for item in EVAL_DATASET if item["difficulty"] == "hard")
    easy_total         = sum(1 for item in EVAL_DATASET if item["difficulty"] == "easy")

    # ── 基线测试 ──────────────────────────────────────────
    print(f"\n🔍 开始基线评估（无 Prompt 工程）...\n")
    baseline_correct      = 0
    baseline_hard_correct = 0
    baseline_easy_correct = 0
    for item in EVAL_DATASET:
        predicted = await classify_intent_baseline(item["message"])
        is_correct = predicted == item["label"]
        if is_correct:
            baseline_correct += 1
            if item["difficulty"] == "hard":
                baseline_hard_correct += 1
            else:
                baseline_easy_correct += 1
        status = "✅" if is_correct else "❌"
        diff_tag = "🔴" if item["difficulty"] == "hard" else "🟢"
        print(f"{status}{diff_tag} [{item['label']} → {predicted}] {item['message'][:50]}")

    baseline_accuracy = baseline_correct / len(EVAL_DATASET)

    # ── 最终对比 ──────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"         {'基线（无增强）':^20} {'RAG 版本':^20}")
    print(f"{'─'*60}")
    print(f"🟢 Easy  {baseline_easy_correct}/{easy_total} = {baseline_easy_correct/easy_total:.0%}{'':>12}{rag_easy_correct}/{easy_total} = {rag_easy_correct/easy_total:.0%}")
    print(f"🔴 Hard  {baseline_hard_correct}/{hard_total} = {baseline_hard_correct/hard_total:.0%}{'':>12}{rag_hard_correct}/{hard_total} = {rag_hard_correct/hard_total:.0%}")
    print(f"{'─'*60}")
    print(f"📊 总计  {baseline_correct}/{len(EVAL_DATASET)} = {baseline_accuracy:.1%}{'':>9}{correct}/{len(EVAL_DATASET)} = {rag_accuracy:.1%}")
    print(f"📈 提升幅度: +{(rag_accuracy - baseline_accuracy):.1%}  (Hard集提升: +{(rag_hard_correct/hard_total - baseline_hard_correct/hard_total):.1%})")
    print(f"{'='*60}")

    with open("eval_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "baseline_accuracy": baseline_accuracy,
            "rag_accuracy": rag_accuracy,
            "improvement": rag_accuracy - baseline_accuracy,
            "correct": correct,
            "baseline_correct": baseline_correct,
            "total": len(EVAL_DATASET),
            "details": results,
        }, f, indent=2, ensure_ascii=False)

    print("\n✅ 评估结果已保存至 eval_results.json")
    return rag_accuracy


if __name__ == "__main__":
    asyncio.run(run_evaluation())
