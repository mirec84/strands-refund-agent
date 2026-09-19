"""Runs three refund scenarios against the steering-guarded support agent
and prints a transcript suitable for pulling into the blog post.
"""

from app import REFUND_LEDGER, build_agent


def run_scenario(title: str, prompt: str, human_response) -> None:
    print("=" * 70)
    print(title)
    print("-" * 70)
    print(f"USER: {prompt}")

    agent = build_agent()
    result = agent(prompt)

    while result.stop_reason == "interrupt":
        for interrupt in result.interrupts:
            reason = interrupt.reason.get("message", "") if interrupt.reason else ""
            print(f"  [INTERRUPT] {interrupt.name}: {reason}")
            decision = human_response(reason)
            print(f"  [HUMAN] approve={decision}")

        responses = [
            {"interruptResponse": {"interruptId": i.id, "response": human_response(
                i.reason.get("message", "") if i.reason else ""
            )}}
            for i in result.interrupts
        ]
        result = agent(responses)

    final_text = "".join(
        block.get("text", "") for block in result.message.get("content", []) if "text" in block
    )
    print(f"AGENT: {final_text}")
    print()


if __name__ == "__main__":
    # Scenario A: under the $100 auto-approve threshold -> should proceed automatically.
    run_scenario(
        "Scenario A: small refund, should proceed automatically",
        "My order ORD-3003 arrived damaged, can I get a refund of $89 for it?",
        human_response=lambda reason: True,
    )

    # Scenario B: over $100 -> should pause for human approval, then proceed once approved.
    run_scenario(
        "Scenario B: refund over $100, should pause for approval (approved)",
        "Please refund $249.99 for order ORD-2002, I was charged twice for the same item.",
        human_response=lambda reason: True,
    )

    # Scenario C: mentions a dispute -> should pause for approval regardless of amount (denied).
    run_scenario(
        "Scenario C: refund reason mentions a dispute, should pause for approval (denied)",
        "Refund $60 for order ORD-1001 -- the customer's bank flagged this as a chargeback dispute.",
        human_response=lambda reason: False,
    )

    print("Refund ledger (approved refunds only):")
    for entry in REFUND_LEDGER:
        print(" ", entry)
