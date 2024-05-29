
from multiplayer_chat.schemas import InputSchema
from multiplayer_chat.utils import Workflow
from typing import Dict

async def run(inputs: InputSchema, nodes, workflow_config, cfg: Dict):

    workflow = Workflow("Multiplayer Chat", workflow_config)

    workflow.add_task(nodes[0], "chat", {"prompt": inputs.prompt})
    workflow.add_task(nodes[1], "chat", {"prompt": inputs.prompt})

    return workflow
