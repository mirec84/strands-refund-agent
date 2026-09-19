import logging

from bedrock_agentcore.runtime import BedrockAgentCoreApp

from app import build_agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = BedrockAgentCoreApp()


@app.entrypoint
async def invoke_agent(payload):
    """AgentCore entrypoint wrapper.

    Expects payload: {"prompt": "Your question here"}

    If the steering handler pauses the agent for human approval, this
    returns a "pending_approval" response instead of a final answer.
    Resuming that approval across a stateless HTTP call needs the pending
    interrupt (and the conversation so far) persisted in AgentCore Memory --
    see the "Making this production ready" section of the post.
    """
    user_prompt = payload.get("prompt") or payload.get("input", "")
    if not user_prompt:
        return {"error": "Missing 'prompt' field in request payload."}

    try:
        agent = build_agent()
        result = agent(user_prompt)

        if result.stop_reason == "interrupt":
            return {
                "status": "pending_approval",
                "interrupts": [
                    {"id": i.id, "name": i.name, "reason": i.reason}
                    for i in result.interrupts
                ],
            }

        output_text = "".join(
            block.get("text", "") for block in result.message.get("content", []) if "text" in block
        )
        return {"status": "success", "response": output_text}
    except Exception as e:
        logger.error(f"Execution error: {str(e)}")
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    app.run()
