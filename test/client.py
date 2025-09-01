from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
import asyncio
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

model = ChatGroq(model_name="llama-3.1-8b-instant", stop_sequences=None)

server_params = StdioServerParameters(
      command="python3",
      args=["math_server.py"]
)

async def run_agent():
      async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                  await session.initialize()
                  tools=await load_mcp_tools(session)
                  agent = create_react_agent(model, tools)
                  agent_response = await agent.ainvoke(
                  {"messages":"what's (4+6)x14?"}
                  )
                  return agent_response["messages"][3].content

if __name__ == "__main__":
      result = asyncio.run(run_agent())
      print(result)
