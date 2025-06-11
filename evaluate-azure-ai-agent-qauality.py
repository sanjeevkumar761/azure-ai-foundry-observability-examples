# Ref: https://github.com/azure/azure-sdk-for-python/issues/41446

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
# Import your custom functions to be used as Tools for the Agent
from user_functions import user_functions

# Load environment variables
load_dotenv()

# Initialize Azure AI clients
endpoint = os.getenv("AZURE_AI_FOUNDRY_PROJECT_ENDPOINT")
credential = DefaultAzureCredential()

agent_client = AgentsClient(endpoint=endpoint, credential=credential)
project_client = AIProjectClient(
    credential=credential,
    endpoint=endpoint,
    api_version="2025-05-15-preview"
)

# Create Agent
agent = agent_client.create_agent(
    model=os.environ["AZURE_OPENAI_MODEL_DEPLOYMENT"],
    name="city-travel-agent",
    instructions="You are helpful agent"
)
print(f"Created agent, ID: {agent.id}")

# Start a conversation thread
thread = agent_client.threads.create()

# Create a user message
MESSAGE = "Tell me about Seattle"
message = agent_client.messages.create(
    thread_id=thread.id,
    role="user",
    content=MESSAGE,
)
print(f"Created message, ID: {message.id}")

# Run the agent
run = agent_client.runs.create(thread_id=thread.id, agent_id=agent.id)
print(f"Run ID: {run.id}")

# Poll the run status
while run.status in ["queued", "in_progress", "requires_action"]:
    time.sleep(1)
    run = agent_client.runs.get(thread_id=thread.id, run_id=run.id)
    print(f"Run status: {run.status}")

if run.status == "failed":
    print(f"Run error: {run.last_error}")

# List messages in the thread
messages = agent_client.messages.list(thread_id=thread.id, order=ListSortOrder.ASCENDING)
for msg in messages:
    if msg.text_messages:
        last_text = msg.text_messages[-1]
        print(f"{msg.role}: {last_text.text.value}")

# Prepare evaluation data
converter = AIAgentConverter(project_client)
filename = os.path.join(os.getcwd(), "evaluation_input_data.jsonl")
evaluation_data = converter.prepare_evaluation_data(thread_ids=thread.id, filename=filename)

with open(filename, "w", encoding='utf-8') as f:
    for obj in evaluation_data:
        f.write(json.dumps(obj, ensure_ascii=False) + '\n')
print(f"Evaluation data saved to {filename}")

# Model configuration for evaluation
model_config = AzureOpenAIModelConfiguration(
    azure_endpoint=os.environ["AZURE_OPENAI_SERVICE"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version="2025-01-01-preview",
    azure_deployment=os.environ["AZURE_OPENAI_CHATGPT_DEPLOYMENT"],
)

# Initialize evaluators
intent_resolution = IntentResolutionEvaluator(model_config=model_config)
tool_call_accuracy = ToolCallAccuracyEvaluator(model_config=model_config)
task_adherence = TaskAdherenceEvaluator(model_config=model_config)

used_evaluators = {
    "tool_call_accuracy": tool_call_accuracy,
    "intent_resolution": intent_resolution,
    "task_adherence": task_adherence,
}

# Run evaluation
response = evaluate(
    data=filename,
    evaluators=used_evaluators,
    azure_ai_project=os.environ.get("AZURE_AI_FOUNDRY_PROJECT_ENDPOINT")
)

# Clean up agent
agent_client.delete_agent(agent.id)

# Output results
pprint(f'AI Foundry URL: {response.get("studio_url")}')
pprint(response["metrics"])
