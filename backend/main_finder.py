# File: main.py (For testing the Doctor Finder Agent)

from typing import TypedDict, Annotated
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_ollama import ChatOllama

# --- Local Imports from our Agent Files ---
# We only need to import the agent we are testing
from agent_finder import DoctorFinderAgent


# --- SHARED AGENT STATE ---
# This state is simplified for this test, but keeps the same structure
class AppState(TypedDict):
    messages: Annotated[list, add_messages]


# --- Graph Definition and Execution ---

# Initialize the model that the agent will use
text_model = ChatOllama(model="llama3.2:3b")

# Instantiate the agent
finder_agent = DoctorFinderAgent(model=text_model)

# Define the graph
workflow = StateGraph(AppState)

# The graph has only one node: the finder agent
workflow.add_node("finder_agent", finder_agent)

# The entry point is the finder agent
workflow.set_entry_point("finder_agent")

# After the agent runs, the process ends
workflow.add_edge("finder_agent", END)

# Compile the final graph
app = workflow.compile()

# --- Main Execution Logic ---
if __name__ == '__main__':
    print("--- Testing Doctor Finder Agent ---")
    print("Make sure your MCP server is running in a separate terminal.")

    # Define the user's query to test the agent
    inputs = {
        "messages": [HumanMessage(content="I have a persistent cough and fever. Can you find a doctor near Bhopal?")]}

    # Invoke the graph
    results = app.invoke(inputs)

    # Print the final response from the agent
    print(f"\nAgent's Response:\n{results['messages'][-1].content}")
    print("-" * 20)
