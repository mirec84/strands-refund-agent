# Strands Refund Agent

A customer-support agent built with [Strands Agents](https://strandsagents.com) that can look up
orders and issue refunds, guarded by Strands' **Steering** handler: a natural-language policy layer
that decides whether each refund can proceed automatically, needs to be guided toward a different
approach, or must pause for human approval.

Companion code for the blog post in `blog.md`.

## Layout

- `app.py` — the agent: tools (`lookup_order`, `issue_refund`) and the steering policy.
- `demo.py` — runs three scenarios locally (auto-approved, human-approved, human-denied) against
  Amazon Bedrock.
- `main.py` — Amazon Bedrock AgentCore Runtime entrypoint.
- `Dockerfile`, `deploy.sh`, `trust-policy.json` — package and deploy `main.py` to AgentCore.

## Running locally

Requires AWS credentials with Bedrock access in `us-east-1` (or edit the `region_name` /
`model_id` in `app.py`).

```bash
pip install -r requirements.txt
python3 demo.py
```

## Deploying

```bash
./deploy.sh
```

See `blog.md` for the full walkthrough, including a note on why resuming a paused
(interrupted) agent across a stateless HTTP call needs session state in AgentCore Memory.
