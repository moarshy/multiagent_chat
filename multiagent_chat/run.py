from multiagent_chat.schemas import InputSchema
from naptha_sdk.task import Task

from typing import Dict
from multiagent_chat.utils import get_logger

logger = get_logger(__name__)

async def run(inputs: InputSchema, worker_nodes, orchestrator_node, flow_run, cfg: Dict):

    agent1 = Task(name="chat_agent_initiator", fn="simple_chat_agent", worker_node=worker_nodes[0], orchestrator_node=orchestrator_node, flow_run=flow_run)
    agent2 = Task(name="chat_agent_receiver", fn="simple_chat_agent", worker_node=worker_nodes[1], orchestrator_node=orchestrator_node, flow_run=flow_run)

    response = await agent1(prompt=inputs.prompt)

    for i in range(10):
        response = await agent2(prompt=response)
        response = await agent1(prompt=response)

    return response

if __name__ == "__main__":
    import asyncio
    from naptha_sdk.client.node import Node
    from naptha_sdk.schemas import AgentRun
    import yaml
    cfg_path = "multiagent_chat/component.yaml"
    with open(cfg_path, "r") as file:
        cfg = yaml.load(file, Loader=yaml.FullLoader)
    args = {
        "prompt": "lets count up one number at a time. ill start. one.",
        "coworkers": "http://node.naptha.ai:7001,http://node1.naptha.ai:7001"
    }
    flow_run = {"consumer_id": "user:18837f9faec9a02744d308f935f1b05e8ff2fc355172e875c24366491625d932f36b34a4fa80bac58db635d5eddc87659c2b3fa700a1775eb4c43da6b0ec270d", "agent_name": "multiagent_chat", "agent_run_type": "package"}
    flow_run = AgentRun(**flow_run)
    inputs = InputSchema(**args)
    orchestrator_node = Node("http://localhost:7001")
    worker_nodes = [Node(coworker) for coworker in args['coworkers'].split(',')]
    response = asyncio.run(run(inputs, worker_nodes, orchestrator_node, flow_run, cfg))
    print(response)
    print("Flow Run: ", flow_run)