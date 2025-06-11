# Agent Evaluation with Azure AI Foundry  

Script: evaluate-azure-ai-agent-qauality.py  

## Overview

This script demonstrates how to create, run, and evaluate an Azure AI Agent using the Azure AI Foundry SDK. It covers the following steps:
- Loading environment variables and initializing Azure AI clients
- Creating an agent and starting a conversation thread
- Sending a user message and running the agent
- Polling for run completion and displaying results
- Preparing evaluation data from the conversation
- Configuring and running multiple evaluators to assess agent quality
- Outputting evaluation results and cleaning up resources

## Prerequisites

- Python environment with required packages (`azure-ai-agents`, `azure-ai-projects`, `azure-ai-evaluation`, `python-dotenv`, etc.)
- Environment variables set for Azure endpoints, credentials, and model deployments
- A `user_functions.py` file with custom tool functions for the agent

## Script Sections

### 1. Imports and Environment Setup

```python
import os
import json
import time
from pprint import pprint
from dotenv import load_dotenv

from azure.identity import DefaultAzureCredential
from azure.ai.agents import AgentsClient
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import ListSortOrder
from azure.ai.evaluation import (
    AIAgentConverter,
    ToolCallAccuracyEvaluator,
    AzureOpenAIModelConfiguration,
    IntentResolutionEvaluator,
    TaskAdherenceEvaluator,
    evaluate,
)
from user_functions import user_functions

# Load environment variables from .env file
load_dotenv()
```

### 2. Azure AI Foundry Agent Client and Project Client Initialization

```python
endpoint = os.getenv("AZURE_AI_FOUNDRY_PROJECT_ENDPOINT")
credential = DefaultAzureCredential()

agent_client = AgentsClient(endpoint=endpoint, credential=credential)
project_client = AIProjectClient(
    credential=credential,
    endpoint=endpoint,
    api_version="2025-05-15-preview"
)
```

### 3. Agent Creation and Conversation Setup

```python
# Create a new agent with specified model and instructions
agent = agent_client.create_agent(
    model=os.environ["AZURE_OPENAI_MODEL_DEPLOYMENT"],
    name="city-travel-agent",
    instructions="You are helpful agent"
)
print(f"Created agent, ID: {agent.id}")

# Start a new conversation thread
thread = agent_client.threads.create()

# Send a user message to the thread
MESSAGE = "Tell me about Seattle"
message = agent_client.messages.create(
    thread_id=thread.id,
    role="user",
    content=MESSAGE,
)
print(f"Created message, ID: {message.id}")
```

### 4. Running the Agent and Polling for Completion

```python
# Run the agent on the conversation thread
run = agent_client.runs.create(thread_id=thread.id, agent_id=agent.id)
print(f"Run ID: {run.id}")

# Poll the run status until completion
while run.status in ["queued", "in_progress", "requires_action"]:
    time.sleep(1)
    run = agent_client.runs.get(thread_id=thread.id, run_id=run.id)
    print(f"Run status: {run.status}")

if run.status == "failed":
    print(f"Run error: {run.last_error}")
```

### 5. Displaying Conversation Messages

```python
# List and print all messages in the thread
messages = agent_client.messages.list(thread_id=thread.id, order=ListSortOrder.ASCENDING)
for msg in messages:
    if msg.text_messages:
        last_text = msg.text_messages[-1]
        print(f"{msg.role}: {last_text.text.value}")
```

### 6. Preparing Evaluation Data

```python
# Convert the conversation thread to evaluation data and save as JSONL
converter = AIAgentConverter(project_client)
filename = os.path.join(os.getcwd(), "evaluation_input_data.jsonl")
evaluation_data = converter.prepare_evaluation_data(thread_ids=thread.id, filename=filename)

with open(filename, "w", encoding='utf-8') as f:
    for obj in evaluation_data:
        f.write(json.dumps(obj, ensure_ascii=False) + '\n')
print(f"Evaluation data saved to {filename}")
```

### 7. Model Configuration and Evaluator Initialization

```python
# Configure the model for evaluation
model_config = AzureOpenAIModelConfiguration(
    azure_endpoint=os.environ["AZURE_OPENAI_SERVICE"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version="2025-01-01-preview",
    azure_deployment=os.environ["AZURE_OPENAI_CHATGPT_DEPLOYMENT"],
)

# Initialize evaluators for different quality metrics
intent_resolution = IntentResolutionEvaluator(model_config=model_config)
tool_call_accuracy = ToolCallAccuracyEvaluator(model_config=model_config)
task_adherence = TaskAdherenceEvaluator(model_config=model_config)

used_evaluators = {
    "tool_call_accuracy": tool_call_accuracy,
    "intent_resolution": intent_resolution,
    "task_adherence": task_adherence,
}
```

### 8. Running Evaluation and Outputting Results

```python
# Run the evaluation using the prepared data and evaluators
response = evaluate(
    data=filename,
    evaluators=used_evaluators,
    azure_ai_project=os.environ.get("AZURE_AI_FOUNDRY_PROJECT_ENDPOINT")
)

# Clean up the created agent
agent_client.delete_agent(agent.id)

# Print evaluation results and metrics
pprint(f'AI Foundry URL: {response.get("studio_url")}')
pprint(response["metrics"])
```

---

## References

- [Azure SDK for Python Issue #41446](https://github.com/azure/azure-sdk-for-python/issues/41446)
- Azure AI Foundry documentation

---

**Note:**  
Replace environment variable values and ensure all dependencies are installed before