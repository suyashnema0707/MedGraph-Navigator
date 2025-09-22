# File: agent_symptom.py

import os
import re
from typing import TypedDict, Annotated

from langchain_core.messages import AIMessage, HumanMessage
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings, ChatOllama


# --- State Definition ---
class AppState(TypedDict):
    messages: Annotated[list, lambda x, y: x + y]
    health_issue: str


# --- Symptom Knowledge Base (for initial filtering) ---
class SymptomKnowledgeBase:
    def __init__(self, file_path="faiss_index", model_name="nomic-embed-text"):
        print("---Symptom Knowledge Base: Initializing---")
        self.retriever = None
        try:
            print(f"Loading pre-processed FAISS index from {file_path}...")
            if not os.path.exists(file_path):
                raise FileNotFoundError("FAISS index directory not found.")

            embedding_model = OllamaEmbeddings(model=model_name)
            vector_store = FAISS.load_local(file_path, embedding_model, allow_dangerous_deserialization=True)
            # Retrieve more candidates for better re-ranking
            self.retriever = vector_store.as_retriever(search_kwargs={'k': 5})
            print("Successfully loaded the symptom knowledge base.")

        except ImportError:
            print("CRITICAL ERROR: The 'faiss-cpu' or 'faiss-gpu' library is not installed.")
        except FileNotFoundError:
            print(f"Error: Could not load the FAISS index from {file_path}.")
        except Exception as e:
            print(f"An error occurred while initializing the Symptom Knowledge Base: {e}")


# --- Global Instances ---
symptom_kb = SymptomKnowledgeBase()


# --- Symptom Identifier Agent with Hierarchical Reasoning ---
class SymptomIdentifierAgent:
    def __init__(self, model: ChatOllama):
        self.model = model

    def __call__(self, state: AppState):
        print("---AGENT 1: Symptom Identifier---")

        user_input = state['messages'][-1].content.lower()
        if "analyze" in user_input and "symptoms" in user_input:
            return {"messages": [
                AIMessage(content="Of course. Please describe the symptoms you are experiencing in detail.")]}

        if not symptom_kb.retriever:
            return {
                "messages": [AIMessage(content="My symptom knowledge base failed to load.")],
                "health_issue": "ERROR: KB_FAILED_TO_LOAD",
            }

        symptoms = state['messages'][-1].content
        print(f"---Agent Logic---: Starting hierarchical search for: '{symptoms}'")

        try:
            # Step 1: Broad candidate retrieval
            retrieved_docs = symptom_kb.retriever.invoke(symptoms)
            if not retrieved_docs:
                raise ValueError("No relevant documents found in the knowledge base.")

            # Step 2: LLM-powered classification into a body system/category
            # --- FIX: Using a much more forceful and specific prompt ---
            classification_prompt = f"""Your task is to classify the following symptoms into one of the provided categories.

            Available Categories:
            - Cardiovascular
            - Neurological
            - Respiratory
            - Dermatological
            - Musculoskeletal
            - Gastrointestinal
            - General/Systemic

            User's Symptoms: "{symptoms}"

            **CRITICAL INSTRUCTION**: Respond with ONLY the single most appropriate category name from the list above. Do not add any explanation or conversational text.
            """
            category_response = self.model.invoke(classification_prompt)
            # Clean the response to ensure it's just one of the categories
            category = category_response.content.strip().split()[0].replace(",", "")
            print(f"---Agent Logic---: Classified symptoms as '{category}'")

            # Step 3: Intelligent Re-ranking using the category as context
            context_for_rerank = ""
            for i, doc in enumerate(retrieved_docs):
                context_for_rerank += f"Option [{i + 1}] (Topic: {doc.metadata['focus_area']})\n"

            rerank_prompt = f"""You are a medical expert. Your task is to perform a differential diagnosis.
            User's Symptoms: "{symptoms}"
            The primary medical category for these symptoms is: "{category}"

            Based on a preliminary search, here are some potentially related health topics:
            {context_for_rerank}

            Considering both the symptoms and the medical category, which topic from the list is the most specific and likely match?
            Respond with ONLY the number of the best match (e.g., "1", "2", etc.).
            """

            best_choice_response = self.model.invoke(rerank_prompt)
            match = re.search(r'\d+', best_choice_response.content)
            if match:
                choice_index = int(match.group(0)) - 1
                if 0 <= choice_index < len(retrieved_docs):
                    identified_issue = retrieved_docs[choice_index].metadata['focus_area']
                    print(f"---Agent Logic---: Final identified issue: {identified_issue}")
                else:
                    raise ValueError("LLM returned an out-of-bounds number.")
            else:
                raise ValueError("Could not parse LLM re-rank response.")

        except Exception as e:
            print(f"---Agent Logic---: Hierarchical search failed: {e}. Using simple top result.")
            retrieved_docs = symptom_kb.retriever.invoke(symptoms)
            identified_issue = retrieved_docs[0].metadata['focus_area'] if retrieved_docs else "Undetermined"

        response_text = (
            f"Based on your symptoms, the potential issue is '{identified_issue}'.\n\n"
            "What would you like to do next?\n"
            "1. Ask a follow-up question.\n"
            "2. Find a doctor for this issue.\n"
            "3. Analyze a different symptom.\n"
            "4. Summarize a medical report."
        )

        return {
            "messages": [AIMessage(content=response_text)],
            "health_issue": identified_issue,
        }

