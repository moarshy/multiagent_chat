from multiagent_chat.schemas import InputSchema
from naptha_sdk.agent import Agent
from naptha_sdk.environment import Environment
import json
from typing import Dict, List
from multiagent_chat.utils import get_logger

logger = get_logger(__name__)

def reverse_roles(messages: List[Dict[str, str]]):
    for msg in messages[1:]:  # Skip the system message
        if msg["role"] == "user":
            msg["role"] = "assistant"
        elif msg["role"] == "assistant":
            msg["role"] = "user"
    return messages

class ChatEnvironment(Environment):
    def __init__(self, db_url: str):
        super().__init__(db_url)

async def run(inputs: InputSchema, worker_node_urls, *args, **kwargs):
    # Initialize environment with database connection
    if not kwargs.get("db_url"):
        raise ValueError("db_url is required")
    
    flow_run = kwargs.get("flow_run")
    flow_id = flow_run.id
    env = ChatEnvironment(kwargs.get("db_url"))
    
    messages = [
        {"role": "user", "content": inputs.prompt},
    ]
    
    # Store initial message
    env.upsert_simulation(flow_id, messages)

    agents = [
        Agent(name="chat_agent_initiator", fn="simple_chat_agent", worker_node_url=worker_node_urls[0], *args, **kwargs),
        Agent(name="chat_agent_receiver", fn="simple_chat_agent", worker_node_url=worker_node_urls[1], *args, **kwargs)
    ]

    for round_num in range(10):
        for agent_num, agent in enumerate(agents):
            response = await agent.call_agent_func(
                tool_name="chat", 
                tool_input_data=messages, 
                llm_backend="openai"
            )
            messages = json.loads(response.results[-1])
            messages = reverse_roles(messages)
            
            # Update database after each agent interaction
            logger.info(f"Updating database for round {round_num}, agent {agent_num}")
            env.upsert_simulation(flow_id, messages)
            
            messages = json.loads(response.results[-1])
    
    return messages

if __name__ == "__main__":
    import asyncio
    from naptha_sdk.client.naptha import Naptha
    from naptha_sdk.client.node import Node
    from naptha_sdk.schemas import AgentRunInput
    import yaml
    import uuid

    naptha = Naptha()

    # Database configuration
    db_url = "postgresql://username:password@localhost:5432/dbname"
    
    # Generate a unique run ID
    run_id = str(uuid.uuid4())

    cfg_path = "multiagent_chat/component.yaml"
    with open(cfg_path, "r") as file:
        cfg = yaml.load(file, Loader=yaml.FullLoader)
    
    inputs = {
        "prompt": "lets count up one number at a time. ill start. one.",
    }

    agent_run = {
        "consumer_id": naptha.user, 
        "agent_name": "multiagent_chat", 
        "agent_run_type": "package", 
        "worker_nodes": ["http://localhost:7001", "http://localhost:7001"]
    }
    agent_run = AgentRunInput(**agent_run)

    inputs = InputSchema(**inputs)
    orchestrator_node = Node("http://localhost:7001")
    
    response = asyncio.run(
        run(
            inputs, 
            worker_node_urls=["http://localhost:7001", "http://localhost:7001"],
            orchestrator_node=orchestrator_node,
            flow_run=agent_run,
            cfg=cfg,
            db_url=db_url,
            run_id=run_id
        )
    )
    print(response)
    print(f"Run ID: {run_id}")  # Save this to retrieve the conversation later