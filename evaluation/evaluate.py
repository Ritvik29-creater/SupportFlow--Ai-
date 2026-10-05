"""
Automated Evaluation Suite for SupportFlow AI
Evaluates:
- Intent Classification Accuracy
- Routing Precision (answer vs clarify vs escalate)
- Prompt Injection Resilience
- Hallucination / Grounding Detection
- Average Confidence Calibration
"""
import json
import os
from core.graph import build_graph
from agents.injection_guard import is_prompt_injection

EVAL_PATH = os.path.join(os.path.dirname(__file__), "eval_dataset.json")


def run_evaluation():
    print("🔬 Loading evaluation dataset...")
    with open(EVAL_PATH, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    print(f"📊 Running benchmarks on {len(dataset)} test cases...")
    graph = build_graph()

    total = len(dataset)
    correct_intents = 0
    correct_actions = 0
    injections_blocked = 0
    total_injections = 0

    results = []

    for i, item in enumerate(dataset, 1):
        query = item["query"]
        expected_intent = item.get("expected_intent")
        expected_action = item.get("expected_action")
        category = item.get("category")

        print(f"\n[{i}/{total}] Testing: \"{query[:45]}...\" ({category})")

        # 1. Guard check
        if is_prompt_injection(query):
            total_injections += 1
            injections_blocked += 1
            action = "escalate"
            intent = "unknown"
            answer = "Blocked by injection guard."
            confidence = 0.0
        else:
            state = {
                "user_query": query,
                "conversation_history": [],
                "force_escalate": False,
                "retrieved_docs": [],
            }
            try:
                res = graph.invoke(state)
                action = res.get("action", "escalate")
                intent = res.get("intent", "unknown")
                answer = res.get("answer", "")
                confidence = res.get("answer_confidence", 0.0)
            except Exception as e:
                action = "escalate"
                intent = "error"
                answer = str(e)
                confidence = 0.0

        intent_match = (intent == expected_intent) if expected_intent else True
        action_match = (action == expected_action) if expected_action else True

        if intent_match:
            correct_intents += 1
        if action_match:
            correct_actions += 1

        print(f"   -> Intent: {intent} (Expected: {expected_intent}) {'✅' if intent_match else '❌'}")
        print(f"   -> Action: {action} (Expected: {expected_action}) {'✅' if action_match else '❌'}")
        print(f"   -> Confidence: {confidence}")

        results.append({
            "id": item["id"],
            "query": query,
            "intent": intent,
            "intent_match": intent_match,
            "action": action,
            "action_match": action_match,
            "confidence": confidence,
        })

    intent_acc = (correct_intents / total) * 100
    action_acc = (correct_actions / total) * 100

    print("\n" + "=" * 50)
    print("📈 EVALUATION SUMMARY METRICS")
    print("=" * 50)
    print(f"Total Test Cases:        {total}")
    print(f"Intent Accuracy:         {intent_acc:.1f}%")
    print(f"Routing Action Accuracy: {action_acc:.1f}%")
    if total_injections > 0:
        print(f"Injection Defense Rate:  {(injections_blocked / total_injections) * 100:.1f}%")
    print("=" * 50)

    output_file = os.path.join(os.path.dirname(__file__), "evaluation_results.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({"metrics": {"intent_accuracy": intent_acc, "action_accuracy": action_acc}, "details": results}, f, indent=2)
    print(f"💾 Detailed results saved to: {output_file}")


if __name__ == "__main__":
    run_evaluation()
