# File: evaluate_models.py

import json
from langchain_ollama import ChatOllama
from langchain_ollama.embeddings import OllamaEmbeddings
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import time

# ===============================================================
# 1. CONFIGURATION
# ===============================================================
# Define the models you want to test in Ollama
FINE_TUNED_MODEL = "monotykamary/medichat-llama3"
BASE_MODEL = "llama3.2:3b"

# Path to your JSON file with test cases
TEST_CASES_FILE = "test_cases_category_1.json"

# The similarity score threshold for an answer to be considered "correct"
SIMILARITY_THRESHOLD = 0.8

# ===============================================================
# 2. SETUP MODELS AND EMBEDDINGS
# ===============================================================
print("--- Initializing models and embedding function ---")

# --- UPDATE: Initialize only one model at a time to save RAM ---
# To test the base model, comment out the fine_tuned_llm and uncomment the base_llm
llm = ChatOllama(model=FINE_TUNED_MODEL)
# llm = ChatOllama(model=BASE_MODEL)

print(f"Successfully connected to model: '{llm.model}'")

# Initialize the embedding model for calculating similarity
try:
    embedding_model = OllamaEmbeddings(model="nomic-embed-text")
    print("Embedding model 'nomic-embed-text' initialized successfully.")
except Exception as e:
    print(f"Error initializing embedding model: {e}")
    print("Please run 'ollama pull nomic-embed-text' before executing this script.")
    exit()


# ===============================================================
# 3. HELPER FUNCTIONS
# ===============================================================
def load_test_cases(file_path):
    """Loads the test cases from a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Test case file not found at '{file_path}'")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Could not decode JSON from '{file_path}'. Error: {e}")
        return None


def get_similarity_score(text1, text2):
    """Calculates the cosine similarity between two texts."""
    try:
        embeddings = embedding_model.embed_documents([text1, text2])
        embedding1 = np.array(embeddings[0]).reshape(1, -1)
        embedding2 = np.array(embeddings[1]).reshape(1, -1)
        return cosine_similarity(embedding1, embedding2)[0][0]
    except Exception as e:
        print(f"Error calculating similarity: {e}")
        return 0.0


# ===============================================================
# 4. EVALUATION SCRIPT
# ===============================================================
def evaluate_model(model_name, llm_instance):
    """Runs the evaluation for a single model and prints the results."""
    test_cases = load_test_cases(TEST_CASES_FILE)
    if not test_cases:
        return

    print(f"\n--- Starting evaluation for {model_name} with {len(test_cases)} test cases ---")

    correct_answers = 0
    total_start_time = time.time()

    prompt_template = """You are a medical expert providing a concise, factual answer to the following question.
Your response should be similar in style and content to a medical textbook or encyclopedia.

Question: {question}

Answer:"""

    for i, case in enumerate(test_cases):
        question = case.get("question")
        expected_answer = case.get("expected_answer")

        if not question or not expected_answer:
            print(f"Skipping malformed test case {i + 1}")
            continue

        prompt = prompt_template.format(question=question)

        print(f"\n--- Test Case {i + 1}/{len(test_cases)} ---")
        print(f"Question: {question}")

        start_time = time.time()
        response = llm_instance.invoke(prompt)
        end_time = time.time()

        score = get_similarity_score(response.content, expected_answer)
        is_correct = score >= SIMILARITY_THRESHOLD
        if is_correct:
            correct_answers += 1

        print(
            f"{model_name} Score: {score:.4f} ({'Correct' if is_correct else 'Incorrect'}) | Time: {end_time - start_time:.2f}s")

    total_end_time = time.time()

    # ===============================================================
    # 5. RESULTS SUMMARY
    # ===============================================================
    print("\n\n" + "=" * 30)
    print(f"--- EVALUATION COMPLETE FOR {model_name} ---")
    print(f"Total Time: {total_end_time - total_start_time:.2f}s")
    print("=" * 30)

    accuracy = (correct_answers / len(test_cases)) * 100

    print(f"\nModel ({model_name}):")
    print(f"  - Correct Answers: {correct_answers}/{len(test_cases)}")
    print(f"  - Accuracy: {accuracy:.2f}%")
    print("\n" + "=" * 30)


if __name__ == "__main__":
    # --- Run the evaluation for the selected model ---
    # To test the base model, comment out the first line and uncomment the second
    evaluate_model(FINE_TUNED_MODEL, llm)
    # evaluate_model(BASE_MODEL, llm)
