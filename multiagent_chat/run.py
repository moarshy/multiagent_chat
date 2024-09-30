from multiagent_chat.schemas import InputSchema
from naptha_sdk.task import Task as Agent

from typing import Dict
from multiagent_chat.utils import get_logger

logger = get_logger(__name__)

async def run(inputs: InputSchema, worker_node_urls, *args, **kwargs):

    agent1 = Agent(name="chat_agent_initiator", fn="simple_chat_agent", worker_node_url=worker_node_urls[0], *args, **kwargs)
    agent2 = Agent(name="chat_agent_receiver", fn="simple_chat_agent", worker_node_url=worker_node_urls[1], *args, **kwargs)

    response = await agent1(prompt=inputs.prompt)

    for i in range(10):
        response = await agent2(prompt=response)
        response = await agent1(prompt=response)

    return response

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
                 "agent_name": "multiagent_chat", "agent_run_type": "package", "worker_node_urls": ["http://node.naptha.ai:7001", "http://node1.naptha.ai:7001"]}
    agent_run = AgentRunInput(**agent_run)
    inputs = InputSchema(**inputs)
    orchestrator_node = Node("http://localhost:7001")
    worker_node_urls = agent_run.worker_node_urls
    response = asyncio.run(run(inputs, agent_run.worker_node_urls, orchestrator_node, agent_run, cfg))
    print(response)
    print("Agent Run: ", agent_run)