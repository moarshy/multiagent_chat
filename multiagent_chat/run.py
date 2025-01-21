import logging
import json
import os
from naptha_sdk.modules.agent import Agent
from naptha_sdk.modules.kb import KnowledgeBase
from naptha_sdk.schemas import OrchestratorRunInput, OrchestratorDeployment, KBRunInput, AgentRunInput
from naptha_sdk.user import sign_consumer_id
from multiagent_chat.schemas import InputSchema
import traceback
from typing import Dict, List
import uuid


logger = logging.getLogger(__name__)
def reverse_roles(messages: List[Dict[str, str]]):
    """Reverse user and assistant roles in messages."""
    for msg in messages[1:]:  # Skip the system message
        if msg["role"] == "user":
            msg["role"] = "assistant"
        elif msg["role"] == "assistant":
            msg["role"] = "user"
    return messages

class MultiAgentChat:
    """Multi-agent chat orchestrator implementation"""
    def __init__(self, orchestrator_deployment: OrchestratorDeployment, *args, **kwargs):
        self.orchestrator_deployment = orchestrator_deployment
        self.agent_deployments = self.orchestrator_deployment.agent_deployments
        self.agents = [
            Agent(deployment=self.agent_deployments[0], *args, **kwargs),
            Agent(deployment=self.agent_deployments[1], *args, **kwargs)
        ]
        self.groupchat_kb = KnowledgeBase(kb_deployment=self.orchestrator_deployment.kb_deployments[0])

    async def run_multiagent_chat(self, module_run: OrchestratorRunInput, *args, **kwargs):

        run_id = str(uuid.uuid4())

        kb_deployment = self.orchestrator_deployment.kb_deployments[0]

        # Create table
        init_result = await self.groupchat_kb.call_kb_func(KBRunInput(
            consumer_id=module_run.consumer_id,
            inputs={"func_name": "init"},
            deployment=kb_deployment.model_dump(),
            signature=sign_consumer_id(module_run.consumer_id, os.getenv("PRIVATE_KEY"))
        ))

        logger.info(f"Init result: {init_result}")

        # Initialize message history
        messages = [
            {"role": "user", "content": module_run.inputs.prompt},
        ]

        add_data_result = await self.groupchat_kb.call_kb_func(KBRunInput(
            consumer_id=module_run.consumer_id,
            inputs={"func_name": "add_data", "func_input_data": {"run_id": run_id, "messages": messages}},
            deployment=kb_deployment.model_dump(),
            signature=sign_consumer_id(module_run.consumer_id, os.getenv("PRIVATE_KEY"))
        ))

        logger.info(f"Add data result: {add_data_result}")

        # Run conversation rounds
        for round_num in range(self.orchestrator_deployment.config.max_rounds):
            for agent_num, agent in enumerate(self.agents):
                try:

                    agent_run_input = AgentRunInput(
                        consumer_id=module_run.consumer_id,
                        inputs={"tool_name": "chat", "tool_input_data": messages},
                        deployment=self.agent_deployments[agent_num],
                        signature=sign_consumer_id(module_run.consumer_id, os.getenv("PRIVATE_KEY"))
                    )

                    # Get agent response
                    response = await agent.call_agent_func(agent_run_input)
                    
                    # Parse and process messages
                    if response.results:
                        messages = json.loads(response.results[-1])
                        messages = reverse_roles(messages)
                        
                        # Update database after each agent interaction
                        logger.info(f"Updating database for round {round_num}, agent {agent_num}")
                        try:
                            await self.groupchat_kb.call_kb_func(KBRunInput(
                                consumer_id=module_run.consumer_id,
                                inputs={"func_name": "add_data", "func_input_data": {"run_id": str(uuid.uuid4()), "messages": messages}},
                                deployment=kb_deployment.model_dump(),
                                signature=sign_consumer_id(module_run.consumer_id, os.getenv("PRIVATE_KEY"))
                            ))
                        except Exception as e:
                            logger.error(f"Failed to update database: {e}")
                            # Continue even if storage fails
                    else:
                        logger.warning(f"No results from agent {agent_num} in round {round_num}")
                        
                except Exception as e:
                    logger.error(f"Error in round {round_num} with agent {agent_num}: {e}")
                    logger.error(f"Full traceback:\n{''.join(traceback.format_tb(e.__traceback__))}")
                    # Continue with next agent/round if one fails
        
        return messages


async def run(module_run: Dict, *args, **kwargs):
    """Run the chat orchestration between two agents."""
    module_run = OrchestratorRunInput(**module_run)
    module_run.inputs = InputSchema(**module_run.inputs)
    multiagent_chat = MultiAgentChat(module_run.deployment)
    messages = await multiagent_chat.run_multiagent_chat(module_run)

    return messages

if __name__ == "__main__":
    import asyncio
    from naptha_sdk.client.naptha import Naptha
    from naptha_sdk.configs import setup_module_deployment

    naptha = Naptha()

    deployment = asyncio.run(setup_module_deployment("orchestrator", "multiagent_chat/configs/deployment.json", node_url = os.getenv("NODE_URL")))

    input_params = {"prompt": "lets count up one number at a time. ill start. one."}
        
    module_run = {
        "inputs": input_params,
        "deployment": deployment,
        "consumer_id": naptha.user.id,
        "signature": sign_consumer_id(naptha.user.id, os.getenv("PRIVATE_KEY"))
    }

    # Run the orchestration
    response = asyncio.run(run(module_run))
    print(response)
        
