"""LangGraph MCP Rescue Agent Node.

This module implements the Level 3 Intelligence layer that talks directly 
to BrowserOS MCP via langchain-mcp-adapters.
"""

import os
from typing import Any, Dict, List, Optional

from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

from src.automation.ariadne.models import AriadneState


class LangGraphBrowserOSAgent:
    """Rescue Agent that talks directly to BrowserOS MCP."""

    def __init__(self, mcp_url: str = "http://127.0.0.1:9000/mcp"):
        self.mcp_url = mcp_url
        # Defaulting to Gemini as seen in requirements.txt
        self.llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro")

    async def run(self, state: AriadneState) -> Dict[str, Any]:
        """Main entry point for the rescue agent node."""
        try:
            # 1. Load tools from BrowserOS MCP
            tools = await load_mcp_tools(self.mcp_url)
            agent = create_react_agent(self.llm, tools)
            
            # 2. Prepare visual and structural context
            prompt = f"Current URL: {state['current_url']}\n"
            prompt += "Goal: Continue the application process.\n"
            prompt += "Analyze the screenshot and DOM to decide the next action."
            
            content = [{"type": "text", "text": prompt}]
            if state.get("screenshot_b64"):
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{state['screenshot_b64']}"}
                })
            
            # 3. Invoke Agent
            inputs = {"messages": [HumanMessage(content=content)]}
            result = await agent.ainvoke(inputs)
            
            # 4. Record success in session memory
            new_memory = state.get("session_memory", {}).copy()
            new_memory["agent_failures"] = 0  # Reset failure count on success
            
            return {
                "history": result["messages"],
                "session_memory": new_memory,
                "errors": []
            }
        except Exception as e:
            # Increment failure counter for circuit breaker
            new_memory = state.get("session_memory", {}).copy()
            new_memory["agent_failures"] = new_memory.get("agent_failures", 0) + 1
            return {
                "errors": [f"AgentRescueError: {str(e)}"],
                "session_memory": new_memory
            }
