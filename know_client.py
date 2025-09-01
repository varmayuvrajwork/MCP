from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
import asyncio
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
import sys
import os
from dotenv import load_dotenv
load_dotenv()

AZURE_API_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_DEPLOYMENT_NAME = os.getenv("AZURE_DEPLOYMENT_NAME", "gpt-4o")
llm = AzureChatOpenAI(
      azure_endpoint=AZURE_ENDPOINT,
      api_key=AZURE_API_KEY,  
      azure_deployment=AZURE_DEPLOYMENT_NAME,
      api_version="2024-12-01-preview"
)

# Update this line to point to your enhanced knowledge server
server_params = StdioServerParameters(
      command="python3",
      args=["server.py"]  # Changed from knowledge_server.py
      )

async def run_agent(query, chat_history=None):
      """
      Run the agent with the given query and optional chat history.
      
      Args:
            query: The user's question or request
            chat_history: List of previous messages in the conversation
      
      Returns:
            The agent's response
      """
      if chat_history is None:
            chat_history = []
      
      async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                  await session.initialize()
                  tools = await load_mcp_tools(session)
                  agent = create_react_agent(llm, tools)
                  
                  # Construct messages from chat history and current query
                  messages = chat_history + [HumanMessage(content=query)]
                  
                  agent_response = await agent.ainvoke({"messages": messages})
                  
                  # Get the last AI message
                  ai_message = agent_response["messages"][-1]
                  return ai_message.content

async def interactive_chat():
      """Run an interactive chat session with the knowledge assistant."""
      print("Enhanced Knowledge Assistant Chatbot")
      print("Ask research questions or type 'exit' to quit.")
      print("=" * 50)
      
      chat_history = []
      
      while True:
            # Get user input
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                  print("\nKnowledge Assistant: Goodbye! Have a great day!")
                  break
            
            try:
                  # Get response from agent
                  response = await run_agent(user_input, chat_history)
                  print(f"\nKnowledge Assistant: {response}")
                  
                  # Update chat history
                  chat_history.append(HumanMessage(content=user_input))
                  chat_history.append(AIMessage(content=response))
                  
                  # Keep history manageable (optional)
                  if len(chat_history) > 10:  # Keep last 5 turns
                        chat_history = chat_history[-10:]
                  
            except Exception as e:
                  print(f"\nError: {e}")

if __name__ == "__main__":
      if len(sys.argv) > 1:
            # Single question mode
            result = asyncio.run(run_agent(" ".join(sys.argv[1:])))
            print(result)
      else:
            # Interactive mode
            asyncio.run(interactive_chat())