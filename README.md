# Multiagent Chat

This is an agent orchestrator module for multiagent chat. You can check out other examples of agent, orchestrator and environment modules using the CLI command with the [Naptha SDK](https://github.com/NapthaAI/naptha-sdk). 

## Running the Agent Orchestrator Module on a Naptha Node

### Pre-Requisites 

#### Install the Naptha SDK

Install the Naptha SDK using the [instructions here](https://github.com/NapthaAI/naptha-sdk).

#### (Optional) Run your own Naptha Node

You can run your own Naptha node using the [instructions here](https://github.com/NapthaAI/node) (still private, please reach out if you'd like access).

### Run the Agent Orchestrator Module

Using the Naptha SDK:

```bash
naptha run orchestrator:multiagent_chat -p "prompt='i would like to count up to ten, one number at a time. ill start. one.'" --worker_nodes "http://node.naptha.ai:7001,http://node1.naptha.ai:7001" --environment_nodes "postgresql://naptha:naptha@localhost:3002/naptha"
```

## Running the Agent Orchestrator Module Locally

### Pre-Requisites 

#### Install Poetry 

From the official poetry [docs](https://python-poetry.org/docs/#installing-with-the-official-installer):

```bash
curl -sSL https://install.python-poetry.org | python3 -
export PATH="/home/$(whoami)/.local/bin:$PATH"
```

### Clone and Install the Agent Orchestrator Module

Clone the module using:

```bash
git clone https://github.com/NapthaAI/multiagent_chat
cd multiagent_chat
```

You can install the module using:

```bash
poetry install
```

### Running the Module

Before deploying to a Naptha node, you should iterate on improvements with the module locally. You can run the module using:

```bash
poetry run python multiagent_chat/run.py
```
