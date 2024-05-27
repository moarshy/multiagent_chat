
import asyncio
from multiplayer_chat.schemas import InputSchema
from multiplayer_chat.utils import get_logger
# from naptha_sdk.client.node import Node
import time
from typing import Dict
import yaml

logger = get_logger(__name__)

async def run(inputs: InputSchema, nodes, workflow_config, cfg: Dict):

    assert nodes is not None, "Multiplayer chat requires input list of node URLs."

    logger.info(f"Coworker Nodes: {nodes[0].node_url}")

    user_input = {
        "public_key": workflow_config["consumer_id"].split(':')[1],
        'id': workflow_config["consumer_id"],
    }

    logger.info(f"Checking user: {user_input}")
    user = await nodes[0].check_user(user_input=user_input)

    if user["is_registered"] == True:
        print("Found user...", user)
    elif user["is_registered"] == False:
        print("No user found. Registering user...")
        user = await nodes[0].register_user(user_input=user)
        print(f"User registered: {user}.")

    task_input = {
        'consumer_id': workflow_config["consumer_id"],
        "module_id": "chat",
        "module_params": {"prompt": inputs.prompt},
    }

    logger.info(f"Running task: {task_input}")
    job = await nodes[0].run_task(task_input=task_input, local=True)
    logger.info(f"Job: {job}")
    while True:
        j = await nodes[0].check_task({"id": job['id']})

        status = j['status']
        logger.info(status)   

        if status == 'completed':
            break
        if status == 'error':
            break

        time.sleep(3)

    if j['status'] == 'completed':
        logger.info(j['reply'])
    else:
        logger.info(j['error_message'])

    print("Checking user...")
    user = await nodes[1].check_user(user_input={
        "public_key": workflow_config["consumer_id"].split(':')[1],
        'id': workflow_config["consumer_id"],
    })

    if user["is_registered"] == True:
        print("Found user...", user)
    elif user["is_registered"] == False:
        print("No user found. Registering user...")
        user = await nodes[1].register_user(user_input=user)
        print(f"User registered: {user}.")

    job = await nodes[1].run_task(task_input={
        'consumer_id': workflow_config["consumer_id"],
        "module_id": "chat",
        "module_params": {"prompt": j['reply']['output']}
    }, local=True)

    logger.info(f"Job ID: {job['id']}")
    while True:
        j = await nodes[1].check_task({"id": job['id']})

        status = j['status']
        logger.info(status)   

        if status == 'completed':
            break
        if status == 'error':
            break

        time.sleep(3)

    if j['status'] == 'completed':
        logger.info(j['reply'])
    else:
        logger.info(j['error_message'])

    return j['reply']

if __name__ == "__main__":
    cfg_path = "multiplayer_chat/component.yaml"
    with open(cfg_path, "r") as file:
        cfg = yaml.load(file, Loader=yaml.FullLoader)


    args = {
        "prompt": "hello, how are you doing?",
        "coworkers": "http://node.naptha.ai:7001,http://node1.naptha.ai:7001"
    }

    job = {"consumer_id": "user:18837f9faec9a02744d308f935f1b05e8ff2fc355172e875c24366491625d932f36b34a4fa80bac58db635d5eddc87659c2b3fa700a1775eb4c43da6b0ec270d"}

    inputs = InputSchema(**args)

    # nodes = [Node(coworker) for coworker in args['coworkers'].split(',')]

    response = asyncio.run(run(inputs, nodes, job, cfg))
    logger.info(response)