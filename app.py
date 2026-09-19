"""Support agent that can issue refunds, guarded by Strands Steering."""

from strands import Agent, tool
from strands.models import BedrockModel
from strands.vended_plugins.steering import LedgerProvider, LLMSteeringHandler

ORDERS = {
    "ORD-1001": {"customer": "Jane Doe", "amount": 42.50, "status": "delivered"},
    "ORD-2002": {"customer": "Sam Lee", "amount": 249.99, "status": "delivered"},
    "ORD-3003": {"customer": "Priya Nair", "amount": 89.00, "status": "delivered"},
}

REFUND_LEDGER: list[dict] = []


@tool
def lookup_order(order_id: str) -> dict:
    """Look up an order by ID and return its customer, amount, and status."""
    print(f"    [tool] lookup_order(order_id={order_id!r})")
    order = ORDERS.get(order_id)
    if not order:
        return {"error": f"No such order: {order_id}"}
    return order


@tool
def issue_refund(order_id: str, amount: float, reason: str) -> str:
    """Issue a refund for an order.

    Args:
        order_id: The order to refund.
        amount: The refund amount in USD.
        reason: Why the refund is being issued.
    """
    print(f"    [tool] issue_refund(order_id={order_id!r}, amount={amount}, reason={reason!r})")
    order = ORDERS.get(order_id)
    if not order:
        return f"Cannot refund unknown order {order_id}"
    if amount > order["amount"]:
        return f"Refund of ${amount:.2f} exceeds the original order amount of ${order['amount']:.2f}"

    REFUND_LEDGER.append({"order_id": order_id, "amount": amount, "reason": reason})
    return f"Refunded ${amount:.2f} to {order['customer']} for order {order_id}. Reason: {reason}"


STEERING_POLICY = """
You are a financial-control reviewer overseeing a customer support agent that can issue refunds.

Policy:
- Refunds of $100 or less may proceed automatically.
- Refunds over $100 must pause for human approval before executing.
- If the stated reason mentions fraud, chargeback, or a dispute, always pause for
  human approval, regardless of amount.
- If the agent tries to issue a refund without first looking up the order, guide it
  to call lookup_order first.

Be concise. When you guide or interrupt, state the specific rule that triggered your decision.
"""


def build_agent() -> Agent:
    steering = LLMSteeringHandler(
        system_prompt=STEERING_POLICY,
        context_providers=[LedgerProvider()],
    )

    return Agent(
        model=BedrockModel(
            model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0", region_name="us-east-1"
        ),
        system_prompt=(
            "You are a helpful customer support agent. You can look up orders and "
            "issue refunds. Always look up an order before refunding it, and use the "
            "customer's own words to inform the refund reason."
        ),
        tools=[lookup_order, issue_refund],
        plugins=[steering],
        callback_handler=None,
    )
