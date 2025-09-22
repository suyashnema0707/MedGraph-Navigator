# File: main.py

import os
import re
from typing import TypedDict, Annotated
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

# --- Load environment variables ---
load_dotenv()

# --- Import all agent classes ---
from agent_symptom import SymptomIdentifierAgent
from agent_rag import RagAgent
from agent_summarizer import MedicalReportSummarizerAgent
from agent_extractor import DataExtractorAgent
from agent_finder import DoctorFinderAgent


# --- State Definition ---
class AppState(TypedDict):
    messages: Annotated[list, lambda x, y: x + y]
    health_issue: str
    extracted_text: str
    image_path: str


# --- Model Initialization ---
print("--- Initializing Models ---")
# Use the specified fine-tuned model for text tasks
text_model = ChatOllama(model="monotykamary/medichat-llama3:8b")
print(f"Text model loaded: {text_model.model}")

# Use a powerful model for the intelligent router and vision tasks
try:
    gemini_model = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", temperature=0)
    print(f"Gemini model loaded: gemini-1.5-flash-latest (used for routing and vision)")
except Exception as e:
    print(f"--- CRITICAL ERROR: Could not initialize Gemini model. ---")
    print("Please make sure your GOOGLE_API_KEY is set in the .env file.")
    print(f"Details: {e}")
    gemini_model = None

# --- Agent Initialization ---
print("\n--- Initializing Agents ---")
symptom_agent = SymptomIdentifierAgent(model=text_model)
rag_agent = RagAgent(model=text_model)
summarizer_agent = MedicalReportSummarizerAgent(model=text_model)
finder_agent = DoctorFinderAgent(model=text_model)
extractor_agent = DataExtractorAgent(model=gemini_model)
print("All agents initialized.")


# --- Router and Handler Functions ---
def intelligent_router(state: AppState) -> str:
    print("---INTELLIGENT ROUTER---")
    if not gemini_model:
        print("Router model (Gemini) not available. Defaulting to symptom agent.")
        return "symptom_agent"

    history = state.get("messages", [])
    health_issue = state.get("health_issue")

    conversation_history = "\n".join(
        [f"{msg.type}: {msg.content}" for msg in history]
    )

    prompt = f"""You are an expert router for a multi-agent healthcare system. Your job is to analyze the conversation and decide which agent should handle the LATEST user message.

    The available agents are:
    - symptom_agent: Use if the user is describing symptoms for the first time or is clearly starting a new symptom analysis.
    - rag_agent: Use ONLY for direct follow-up questions AFTER a `health_issue` has been identified.
    - finder_agent: Use when the user asks to find a doctor, specialist, or clinic. Also use if the user is providing a location after being asked for one.
    - summarizer_agent: Use if the user pastes a large block of text that looks like a medical report.

    Here is the current state of the conversation:
    - Currently Identified Health Issue: "{health_issue or 'None'}"

    Here is the full conversation history:
    {conversation_history}

    **CRITICAL INSTRUCTION**: Analyze the LAST user message in the history.
    - If a `health_issue` is present and the last user message is a question about it (like "what are the causes" or "1"), route to `rag_agent`.
    - If the user asks to find a doctor (like "find a specialist" or "2"), route to `finder_agent`.
    - If the user provides a large block of text with medical terms, route to `summarizer_agent`.
    - If the user's first message describes symptoms, route to `symptom_agent`.
    - If the conversation history is empty or the user intent is unclear, default to `symptom_agent`.

    Based on the LATEST user message and the full conversation context, which agent should be called next?
    Respond with ONLY the name of the agent. For example: 'symptom_agent'.
    """

    try:
        response = gemini_model.invoke(prompt)
        decision = response.content.strip().replace("'", "").replace("`", "")

        valid_agents = ["symptom_agent", "rag_agent", "finder_agent", "summarizer_agent"]
        for agent in valid_agents:
            if agent in decision:
                print(f"Router Decision: {agent}")
                return agent

        print(f"Router returned an invalid decision: '{decision}'. Defaulting to symptom_agent.")
        return "symptom_agent"

    except Exception as e:
        print(f"Error during intelligent routing: {e}")
        return "symptom_agent"


def after_extraction(state: AppState) -> str:
    extracted_text = state.get("extracted_text", "").lower()
    expected_keywords = ["patient", "report", "lab", "doctor", "impression", "results", "clinical"]

    if not extracted_text or not any(keyword in extracted_text for keyword in expected_keywords):
        print("---Extraction Failure or Hallucination Detected---")
        state['messages'].append(AIMessage(
            content="I was unable to read the provided medical report image, or the content was not recognized as a report. Please try again with a clearer image."))
        state['image_path'] = ""
        return END
    else:
        print("---Extraction Success---")
        state['messages'][-1] = HumanMessage(content=state['extracted_text'])
        return "summarizer_agent"


# --- Graph Definition ---
graph_builder = StateGraph(AppState)

# Add all the specialist agent nodes
graph_builder.add_node("symptom_agent", symptom_agent)
graph_builder.add_node("rag_agent", rag_agent)
graph_builder.add_node("finder_agent", finder_agent)
graph_builder.add_node("summarizer_agent", summarizer_agent)
graph_builder.add_node("extractor_agent", extractor_agent)


def entry_point_router(state: AppState):
    """First router to decide between image processing and text routing."""
    if state.get("image_path"):
        return "extractor_agent"
    return intelligent_router(state)


# Set the conditional entry point for the graph
graph_builder.set_conditional_entry_point(
    entry_point_router,
    {
        "extractor_agent": "extractor_agent",
        "symptom_agent": "symptom_agent",
        "rag_agent": "rag_agent",
        "finder_agent": "finder_agent",
        "summarizer_agent": "summarizer_agent",
    },
)

# --- FIX: All agents now go to END after they run ---
# This stops the infinite loop and sends the response back to the user.
# The router is only used at the beginning of a new turn.
graph_builder.add_edge("symptom_agent", END)
graph_builder.add_edge("rag_agent", END)
graph_builder.add_edge("finder_agent", END)
graph_builder.add_edge("summarizer_agent", END)

# The extractor has a special conditional edge that can either end or go to the summarizer
graph_builder.add_conditional_edges(
    "extractor_agent",
    after_extraction,
    {
        "summarizer_agent": "summarizer_agent",
        END: END
    }
)

app = graph_builder.compile()
print("\n--- LangGraph App Compiled ---")

