"""LangGraph MCP Rescue Agent Node.

This module implements the Level 3 Intelligence layer that talks directly
to BrowserOS MCP via langchain-mcp-adapters.
"""

import os
from typing import Any, Dict, List, Optional

from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from src.automation.ariadne.models import AriadneState
from src.automation.ariadne.config import get_gemini_model


class LangGraphBrowserOSAgent:
    """Rescue Agent that talks directly to BrowserOS MCP."""

    def __init__(self, mcp_url: str = "http://127.0.0.1:9000/mcp"):
        self.mcp_url = mcp_url
        self.llm = ChatGoogleGenerativeAI(model=get_gemini_model())

    async def run(self, state: AriadneState) -> Dict[str, Any]:
        """Main entry point for the rescue agent node."""
        try:
            # 1. Load tools from BrowserOS MCP
            tools = await load_mcp_tools(self.mcp_url)
            llm_with_tools = self.llm.bind_tools(tools)

            # 2. Prepare visual and structural context
            prompt = f"Current URL: {state['current_url']}\n"
            prompt += "Goal: Continue the application process.\n"
            prompt += "Analyze the screenshot and DOM to decide the next action."

            messages = state.get("history", [])
            if not messages:
                content = [{"type": "text", "text": prompt}]
                if state.get("screenshot_b64"):
                    content.append(
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{state['screenshot_b64']}"
                            },
                        }
                    )
                messages = [HumanMessage(content=content)]

            # 3. Simple React Loop (Max 5 turns for one node visit)
            new_messages = []
            for _ in range(5):
                response = await llm_with_tools.ainvoke(messages + new_messages)
                new_messages.append(response)

                if not response.tool_calls:
                    break

                for tool_call in response.tool_calls:
                    # Find tool
                    tool = next((t for t in tools if t.name == tool_call["name"]), None)
                    if tool:
                        result = await tool.ainvoke(tool_call["args"])
                        new_messages.append(
                            ToolMessage(
                                tool_call_id=tool_call["id"], content=str(result)
                            )
                        )
                    else:
                        new_messages.append(
                            ToolMessage(
                                tool_call_id=tool_call["id"],
                                content=f"Error: Tool {tool_call['name']} not found.",
                            )
                        )

            # 4. Record success in session memory
            new_memory = state.get("session_memory", {}).copy()
            new_memory["agent_failures"] = 0  # Reset failure count on success

            return {"history": new_messages, "session_memory": new_memory, "errors": []}
        except Exception as e:
            # Increment failure counter for circuit breaker
            new_memory = state.get("session_memory", {}).copy()
            new_memory["agent_failures"] = new_memory.get("agent_failures", 0) + 1
            return {
                "errors": [f"AgentRescueError: {str(e)}"],
                "session_memory": new_memory,
            }
