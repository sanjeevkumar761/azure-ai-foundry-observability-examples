"""
Tracing Example with LangGraph, Azure AI Foundry, and OpenTelemetry

This script demonstrates how to build a conversational agent using LangGraph and Azure OpenAI, 
while collecting telemetry with Azure Monitor and OpenTelemetry. The agent can answer user questions 
and use a search tool for information retrieval, with all interactions traced for observability.

Key Components:
---------------
- Azure AI Foundry: Used for project management and telemetry connection.
- OpenTelemetry & Azure Monitor: Collects and exports traces for observability.
- LangGraph: Manages the conversational agent's state and flow.
- Azure OpenAI: Provides the language model for the agent.
- TavilySearchResults: A search tool integrated into the agent for external information retrieval.

Workflow:
---------
1. Loads environment variables and configures Azure tracing.
2. Initializes Azure AIProjectClient and retrieves the Application Insights connection string.
3. Configures OpenTelemetry to export traces to Azure Monitor.
4. Defines a LangGraph state and builds a conversational agent graph:
    - The agent can answer questions and use a search tool.
    - All interactions are traced and logged.
5. Runs a test interaction with a sample question.

Usage:
------
- Ensure environment variables for Azure credentials and endpoints are set.
- Application Insights must be enabled in your Azure AI Foundry project.
- Run the script to see the agent in action and traces exported to Azure Monitor.

Main Functions:
---------------
- setup_graph(): Builds and compiles the LangGraph agent with tools and model.
- test_agent(graph, question): Runs the agent on a question, printing responses and tracing events.
- main(): Initializes the agent and runs test questions.

Dependencies:
-------------
- azure-ai-projects
- azure-identity
- azure-monitor-opentelemetry
- opentelemetry
- langgraph
- langchain_openai
- langchain_community
- python-dotenv


"""

import os, time
import asyncio
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace
from azure.ai.agents.models import ListSortOrder
from opentelemetry.trace import SpanKind
import os
from dotenv import load_dotenv
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import AzureChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.prebuilt import ToolNode, tools_condition
tracer = trace.get_tracer(__name__)
load_dotenv()

os.environ["AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED"] = "true"

# Initialize the AIProjectClient with Azure credentials and project endpoint
ai_project = AIProjectClient(
    credential=DefaultAzureCredential(),
    endpoint=os.getenv("AZURE_AI_FOUNDRY_PROJECT_ENDPOINT"),
    api_version = "2025-05-15-preview" 
)

connection_string = ai_project.telemetry.get_connection_string()



if not connection_string:
    print("Application Insights is not enabled. Enable by going to Tracing in your Azure AI Foundry project.")
    exit()

# Configure OpenTelemetry to use Azure Monitor for telemetry collection
configure_azure_monitor(connection_string=connection_string) #enable telemetry collection

span = trace.get_current_span()


# Define the state structure for our LangGraph Agent
class State(TypedDict):
    messages: Annotated[list, add_messages]

model = AzureChatOpenAI(
    azure_deployment=os.getenv("AZURE_OPENAI_CHATGPT_DEPLOYMENT"),
    api_version="2024-12-01-preview",
    temperature=0.3,
    azure_endpoint=os.getenv("AZURE_OPENAI_SERVICE")
)

def setup_graph():
    # Initialize our state graph
    graph_builder = StateGraph(State)

    # Set up the search tool
    tool = TavilySearchResults(max_results=2)
    tools = [tool]

    # Set up the AI model
    llm = model
  
    # Connect the tools to our AI model
    llm_with_tools = llm.bind_tools(tools)

    # Define the chatbot node function
    def chatbot(state: State):
        return {"messages": [llm_with_tools.invoke(state["messages"])]}

    # Build the graph structure
    graph_builder.add_node("chatbot", chatbot)
    graph_builder.add_node("tools", ToolNode(tools=[tool]))
    graph_builder.add_conditional_edges("chatbot", tools_condition)
    graph_builder.add_edge("tools", "chatbot")
    graph_builder.add_edge(START, "chatbot")

    return graph_builder.compile()

def test_agent(graph, question: str):
    with tracer.start_as_current_span("langgraph_movie_agent") as span:
        print("\n" + "="*50)
        print(f"😀 User: {question}")
        span.set_attribute("user_input", question)
        print("="*50)

        try:
            for event in graph.stream({"messages": [("human", question)]}):
                for value in event.values():
                    if "messages" in value:
                        message = value["messages"][-1]
                        if hasattr(message, "content"):
                            print("\n🤖 AI:", message.content)
                            span.set_attribute("agent_response", message.content)
                        if hasattr(message, "tool_calls") and message.tool_calls:
                            print("\n🔍 Searching...")
                            for tool_call in message.tool_calls:
                                print(f"- Search query: {tool_call['args'].get('query', '')}")
                                span.set_attribute("search_tool_call_query", f"- Search query: {tool_call['args'].get('query', '')}")
        except Exception as e:
            print(f"\n❌ Error occurred: {str(e)}")


def main():
    test_questions = [
        "What are three popular movies in Switzerland right now?"
    ]

    print("🔄 Initializing agent...")
    graph = setup_graph()
    print("✅ Agent ready!\n")

    for question in test_questions:
        test_agent(graph, question)
        print("\n" + "-"*50)

# Run the main function
if __name__ == "__main__":
    main()