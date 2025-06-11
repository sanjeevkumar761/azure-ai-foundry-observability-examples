# Azure AI Foundry Observability

This project demonstrates how to enable observability and tracing for AI agents and conversational workflows using Azure AI Foundry, OpenTelemetry, and Azure Monitor. It includes example scripts for integrating telemetry into AI agent services and LangGraph-based conversational agents.

## Demo Video
[![Watch the demo video](https://img.youtube.com/vi/Qa1wL7Iahfg/0.jpg)](https://www.youtube.com/watch?v=Qa1wL7Iahfg)

# Link to Agent Evaluation
[Agent Evaluation](AGENT_EVALUATION.md)

## Features

- **OpenTelemetry Tracing**: Collects and exports traces for AI agent interactions.
- **Azure Monitor Integration**: Sends telemetry data to Azure Application Insights for monitoring and analysis.
- **LangGraph Example**: Shows how to build a conversational agent with LangGraph, Azure OpenAI, and integrated observability.
- **AI Agent Service Example**: Demonstrates tracing and observability for a financial education agent.

## Example Scripts

- `tracing-example-ai-agent-service.py`:  
  Demonstrates tracing for an AI agent that provides financial education, including agent creation, conversation management, and telemetry export.

- `tracing-example-langgraph.py`:  
  Shows how to build a conversational agent using LangGraph and Azure OpenAI, with all interactions traced and exported to Azure Monitor.

## Requirements

- Python 3.8+
- Azure SDK for Python:
  - `azure-ai-projects`
  - `azure-identity`
  - `azure-monitor-opentelemetry`
  - `opentelemetry`
  - `langgraph`
  - `langchain_openai`
  - `langchain_community`
  - `python-dotenv`

Install dependencies with:

```sh
pip install -r requirements.txt  
```

For AI Agent tracing with Azure AI Agent service in tracing-example-ai-agent-service.py, you need to - 

```sh
pip install azure-ai-projects==1.0.0b11
```   

## Setup

1. **Environment Variables**:  
   Copy `.env-sample` to `.env` and fill in the required Azure credentials and endpoints.

2. **Azure Resources**:  
   - Ensure you have an Azure AI Foundry project with Application Insights enabled.
   - Set up Azure OpenAI and other required services.

3. **Run Examples**:  
   Execute the example scripts to see observability in action:

   ```sh
   python tracing-example-ai-agent-service.py
   python tracing-example-langgraph.py
   ```

## References

- [Azure AI Foundry Documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/what-is-azure-ai-foundry/)
- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)
- [Azure Monitor](https://learn.microsoft.com/en-us/azure/azure-monitor/)
- [LangGraph](https://github.com/langchain-ai/langgraph)

---

*This project is for demonstration and educational purposes. The included agents provide general information and always include disclaimers where appropriate.*