from multiagent_chat.schemas import InputSchema
from naptha_sdk.task import Task as Agent
import json
from typing import Dict, List
from multiagent_chat.utils import get_logger

logger = get_logger(__name__)

def reverse_roles(messages: List[Dict[str, str]]):
    messages = json.loads(messages)
    for msg in messages[1:]:  # Skip the system message
        if msg["role"] == "user":
            msg["role"] = "assistant"
        elif msg["role"] == "assistant":
            msg["role"] = "user"
    return messages

async def run(inputs: InputSchema, worker_node_urls, *args, **kwargs):

    name1 = "chat_agent_initiator"
    name2 = "chat_agent_receiver"

    print("args: ", args)
    print("kwargs: ", kwargs)
    agent1 = Agent(name=name1, fn="simple_chat_agent", worker_node_url=worker_node_urls[0], *args, **kwargs)
    agent2 = Agent(name=name2, fn="simple_chat_agent", worker_node_url=worker_node_urls[1], *args, **kwargs)

    messages = [
        {"role": "user", "content": inputs.prompt},
    ]

    messages = await agent1(messages=messages)

    for i in range(10):
        messages = reverse_roles(messages)
        messages = await agent2(messages=messages)
        messages = reverse_roles(messages)
        messages = await agent1(messages=messages)

    return messages

if __name__ == "__main__":
    import asyncio
    from naptha_sdk.client.node import Node
    from naptha_sdk.schemas import AgentRunInput
    import yaml
    cfg_path = "multiagent_chat/component.yaml"
    with open(cfg_path, "r") as file:
        cfg = yaml.load(file, Loader=yaml.FullLoader)
    inputs = {
        "prompt": "lets count up one number at a time. ill start. one.",
        
    }
    agent_run = {"consumer_id": "user:18837f9faec9a02744d308f935f1b05e8ff2fc355172e875c24366491625d932f36b34a4fa80bac58db635d5eddc87659c2b3fa700a1775eb4c43da6b0ec270d", 
                 "agent_name": "multiagent_chat", "agent_run_type": "package", "worker_nodes": ["http://localhost:7001", "http://localhost:7001"]}
    agent_run = AgentRunInput(**agent_run)
    inputs = InputSchema(**inputs)
    orchestrator_node = Node("http://localhost:7001")
    response = asyncio.run(run(inputs, worker_node_urls=["http://localhost:7001", "http://localhost:7001"], orchestrator_node=orchestrator_node, flow_run=agent_run, cfg=cfg))
    print(response)
    print("Agent Run: ", agent_run)