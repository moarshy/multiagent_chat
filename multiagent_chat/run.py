import json
from naptha_sdk.agent import Agent
from naptha_sdk.environment import Environment
from naptha_sdk.schemas import OrchestratorRunInput
from multiagent_chat.schemas import InputSchema
from multiagent_chat.utils import get_logger
from typing import Dict, List

logger = get_logger(__name__)

def reverse_roles(messages: List[Dict[str, str]]):
    for msg in messages[1:]:  # Skip the system message
        if msg["role"] == "user":
            msg["role"] = "assistant"
        elif msg["role"] == "assistant":
            msg["role"] = "user"
    return messages

class ChatEnvironment(Environment):
    """Chat-specific environment implementation"""
    pass  # Inherits all functionality from base Environment class

async def run(orchestrator_run: OrchestratorRunInput, *args, **kwargs):
    if not orchestrator_run.environment_deployments[0].environment_node_url:
        raise ValueError("environment_node_url is required")
    
    run_id = orchestrator_run.id

    # Initialize environment - no need for create() since __init__ handles table creation
    env = await ChatEnvironment.create(orchestrator_run)
    
    messages = [
        {"role": "user", "content": orchestrator_run.inputs.prompt},
    ]
    
    # Store initial message
    await env.upsert_simulation(run_id, messages)

    agents = [
        Agent(orchestrator_run=orchestrator_run, agent_index=0, *args, **kwargs),
        Agent(orchestrator_run=orchestrator_run, agent_index=1, *args, **kwargs)
    ]

    for round_num in range(10):
        for agent_num, agent in enumerate(agents):
            response = await agent.call_agent_func(
                tool_name="chat", 
                tool_input_data=messages, 
            )
            messages = json.loads(response.results[-1])
            messages = reverse_roles(messages)
            
            # Update database after each agent interaction
            logger.info(f"Updating database for round {round_num}, agent {agent_num}")
            await env.upsert_simulation(run_id, messages)
            
            messages = json.loads(response.results[-1])
    
    return messages

if __name__ == "__main__":
    import asyncio
    from naptha_sdk.client.naptha import Naptha
    from naptha_sdk.configs import load_agent_deployments, load_environment_deployments, load_orchestrator_deployments
    from naptha_sdk.schemas import OrchestratorRun
    import uuid

    naptha = Naptha()

    input_params = InputSchema(prompt="lets count up one number at a time. ill start. one.")
        
    # Configs
    agent_deployments = load_agent_deployments("multiagent_chat/configs/agent_deployments.json", load_persona_data=False, load_persona_schema=False)
    orchestrator_deployments = load_orchestrator_deployments("multiagent_chat/configs/orchestrator_deployments.json")
    environment_deployments = load_environment_deployments("multiagent_chat/configs/environment_deployments.json")

    orchestrator_run = OrchestratorRun(
        inputs=input_params,
        agent_deployments=agent_deployments,
        orchestrator_deployment=orchestrator_deployments[0],
        environment_deployments=environment_deployments,
        consumer_id=naptha.user.id,
    )

    orchestrator_run.id = str(uuid.uuid4())

    response = asyncio.run(run(orchestrator_run))
    print(response)