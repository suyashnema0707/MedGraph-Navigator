# File: agent_router.py

from typing import TypedDict, Annotated
from langchain_core.messages import AIMessage, HumanMessage
from langchain_ollama import ChatOllama


class AppState(TypedDict):
    messages: Annotated[list, lambda x, y: x + y]
    # ... other state fields


class RouterAgent:
    """
    This agent acts as a "meta-agent" or a central router.
    It uses an LLM to decide which specialist agent should be called next.
    """

    def __init__(self, model: ChatOllama):
        self.model = model

    def __call__(self, state: AppState):
        print("---ROUTER AGENT---")

        # This prompt explains the capabilities of each agent to the router LLM.
        router_prompt = f"""
        You are an expert at routing user requests to the correct specialist agent.
        Based on the conversation history, choose the single most appropriate agent to handle the user's latest message.
        You have the following agents to choose from:

        1.  **symptom_agent**: Use this for the initial analysis of a user's health symptoms when no specific health issue has been identified yet.
        2.  **rag_agent**: Use this for follow-up questions after a health issue has already been identified.
        3.  **finder_agent**: Use this when the user asks to find a doctor, clinic, or specialist in a specific location.
        4.  **summarizer_agent**: Use this ONLY when the user provides a medical report (usually from an image) to be summarized.

        Conversation History:
        {state['messages']}

        Based on the last user message, which agent should be called next?
        Respond with ONLY the name of the agent (e.g., "symptom_agent", "rag_agent", "finder_agent", "summarizer_agent").
        """

        response = self.model.invoke(router_prompt)
        # The response from the LLM is the name of the next node to call.
        return response.content.strip()
