# File: agent_rag.py

import pandas as pd
from typing import TypedDict, Annotated, Dict, List

from langchain_core.messages import AIMessage, HumanMessage
from langchain.tools import tool
from langchain_ollama import ChatOllama


# In a larger project, this AppState could be in a shared types.py file
class AppState(TypedDict):
    messages: Annotated[list, lambda x, y: x + y]
    health_issue: str


# --- CSV Knowledge Base (for initial filtering) ---
class CSVKnowledgeBase:
    def __init__(self, file_path: str):
        print("---CSV Knowledge Base: Initializing---")
        self.data: Dict[str, List[str]] = {}
        try:
            df = pd.read_csv(file_path)
            df.dropna(subset=['focus_area', 'answer'], inplace=True)

            for index, row in df.iterrows():
                focus_area = row['focus_area']
                answer = row['answer']
                if focus_area not in self.data:
                    self.data[focus_area] = []
                self.data[focus_area].append(answer)

            print(f"Successfully loaded and indexed {len(self.data)} unique health issues from CSV.")

        except FileNotFoundError:
            print(f"CRITICAL ERROR: The knowledge base file was not found at {file_path}.")
        except Exception as e:
            print(f"An error occurred while loading the CSV knowledge base: {e}")

    def get_all_context_for_issue(self, health_issue: str) -> str:
        """Retrieves all answer documents for a given health issue and combines them."""
        docs = self.data.get(health_issue, [])
        if not docs:
            return f"I could not find a knowledge base for '{health_issue}'. Please consult a healthcare professional."
        return "\n\n---\n\n".join(docs)


# --- Global Instances and Initialization ---
knowledge_base = CSVKnowledgeBase(file_path="medquad.csv")


# --- RAG Agent Class with Simplified, More Robust Logic ---
class RagAgent:
    """Agent 2: Answers questions using direct context lookup and a focused synthesis prompt."""

    def __init__(self, model: ChatOllama):
        self.model = model

    def __call__(self, state: AppState):
        print("---AGENT 2: RAG Health Agent---")

        user_question = state['messages'][-1].content
        health_issue_context = state['health_issue']

        # Step 1: Retrieve ALL context for the topic. This is more reliable.
        retrieved_context = knowledge_base.get_all_context_for_issue(health_issue_context)

        # Step 2: Re-frame the user's question to be more explicit for the LLM
        reframed_question = f"What is the answer to the question '{user_question}' in the context of '{health_issue_context}'?"

        # Step 3: Use a much better prompt to get a specific, concise answer.
        synthesis_prompt = f"""
        You are an answer-finding assistant. Your task is to provide a direct and concise answer to the user's question using ONLY the provided context.

        **Context:**
        ---
        {retrieved_context}
        ---

        **User's Question (Re-framed for clarity):**
        ---
        {reframed_question}
        ---

        Based **only** on the context provided above, give a specific and focused answer to the user's question. Do not provide a general summary. If the context does not contain a direct answer, state that the information is not available in the provided text.
        """

        # Step 4: Invoke the LLM with the improved prompt
        final_response = self.model.invoke([HumanMessage(content=synthesis_prompt)])

        return {"messages": [final_response]}
