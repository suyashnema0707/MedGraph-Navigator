# This script is designed to be run in a Google Colab notebook.
# Ensure the runtime is set to T4 GPU and you have set your GROQ_API_KEY in Colab's secrets.

# #################################################################
# 1. UPLOAD YOUR TEST CASES FILE
# #################################################################
from google.colab import files
import os

print("--- Please upload your 'test_cases_category_1.json' file ---")
uploaded = files.upload()

TEST_CASES_FILE = "test_cases_category_1.json"
if TEST_CASES_FILE not in uploaded:
    print(f"❌ ERROR: File '{TEST_CASES_FILE}' not found. Please upload the correct file.")
    exit()
else:
    print(f"✅ File '{TEST_CASES_FILE}' uploaded successfully.\n")


# #################################################################
# 2. SETUP: Install Ollama and Python libraries
# #################################################################
print("--- Step 2: Installing Ollama and Python libraries ---")
!curl -fsSL https://ollama.com/install.sh | sh
!pip install -qU langchain-ollama langchain-groq scikit-learn

# Start Ollama in the background
import time
os.system("nohup ollama serve > ollama.log 2>&1 &")
time.sleep(10) # Give the server a moment to start

# --- Server Health Check ---
print("--- Checking if Ollama server is running ---")
try:
    import requests
    response = requests.get("http://127.0.0.1:11434")
    if response.status_code == 200:
        print("✅ Ollama server is running successfully.")
    else:
        print(f"⚠️ Ollama server responded with status code: {response.status_code}")
except requests.exceptions.ConnectionError:
    print("❌ CRITICAL ERROR: Could not connect to Ollama server.")
print("--- Ollama setup complete ---\n")


# #################################################################
# 3. PULL MODELS: Download the models into the Colab environment
# #################################################################
print("--- Step 3: Pulling required Ollama models ---")
!ollama pull monotykamary/medichat-llama3:8b
!ollama pull llama3.2:3b
print("--- All models pulled successfully ---\n")


# #################################################################
# 4. EVALUATION SCRIPT: The main testing logic
# #################################################################
import json
import re
import torch
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq
from google.colab import userdata # For accessing secrets

print("--- Step 4: Starting the evaluation script ---")

# --- Configuration ---
FINE_TUNED_MODEL = "monotykamary/medichat-llama3:8b"
BASE_MODEL = "llama3:8b"
JUDGE_MODEL = "llama3-70b-8192"
NUM_TEST_CASES_TO_RUN = -1 # Set to -1 to run all

# --- Initialize Judge Model ---
print("--- Initializing Judge model ---")
try:
    groq_api_key = userdata.get('GROQ_API_KEY')
    judge_llm = ChatGroq(
        temperature=0,
        model_name=JUDGE_MODEL,
        api_key=groq_api_key
    )
    print(f"Successfully connected to judge model: '{JUDGE_MODEL}' on Groq.")
except Exception as e:
    print(f"--- CRITICAL ERROR: Could not get GROQ_API_KEY. ---")
    print("Please set the GROQ_API_KEY in Colab's secrets (🔑 icon on the left).")
    print(f"Details: {e}")
    exit()

# --- Helper Functions ---
def load_test_cases(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading test cases: {e}")
        return None

def parse_judge_response(response_text):
    try:
        score_match = re.search(r'\d+', response_text)
        if score_match:
            return int(score_match.group(0))
        return 0
    except Exception:
        return 0

# --- Main Evaluation Logic ---
def evaluate_model(model_name, llm_instance, test_cases):
    """Runs the evaluation for a single model and returns the average score."""
    print(f"\n--- Starting evaluation for {model_name} with {len(test_cases)} test cases ---")
    scores = []

    generation_prompt_template = "Question: {question}\nAnswer:"
    judge_prompt_template = """You are an expert medical evaluator. Provide a score from 1 to 5 for the generated answer based on its factual correctness and relevance compared to the expected answer.

Question: "{question}"
Expected Answer: "{expected_answer}"
Generated Answer: "{generated_answer}"

Respond with ONLY the score and a brief justification, like this:
Score: 4
Justification: The answer is factually correct but misses some minor details.
"""

    for i, case in enumerate(test_cases):
        question = case["question"]
        expected_answer = case["expected_answer"]
        generation_prompt = generation_prompt_template.format(question=question)

        print(f"\n--- Test Case {i+1}/{len(test_cases)}: {question} ---")

        generated_response = llm_instance.invoke(generation_prompt).content

        judge_prompt = judge_prompt_template.format(
            question=question,
            expected_answer=expected_answer,
            generated_answer=generated_response
        )

        judge_response = judge_llm.invoke(judge_prompt).content
        score = parse_judge_response(judge_response)
        scores.append(score)

        print(f"{model_name} Score: {score}/5")
        print(f"  - Justification: {judge_response.split('Justification:')[-1].strip()}")

    avg_score = sum(scores) / len(scores) if scores else 0
    return avg_score

# --- Run the full evaluation workflow ---
def run_full_evaluation():
    all_test_cases = load_test_cases(TEST_CASES_FILE)
    if not all_test_cases:
        return

    test_cases = all_test_cases[:NUM_TEST_CASES_TO_RUN] if NUM_TEST_CASES_TO_RUN > 0 else all_test_cases

    results = {}

    # --- Evaluate Fine-Tuned Model ---
    print("\n" + "="*50)
    print(f"--- INITIALIZING FINE-TUNED MODEL: {FINE_TUNED_MODEL} ---")
    print("="*50)
    fine_tuned_llm = ChatOllama(model=FINE_TUNED_MODEL)
    ft_avg_score = evaluate_model(FINE_TUNED_MODEL, fine_tuned_llm, test_cases)
    results[FINE_TUNED_MODEL] = ft_avg_score
    del fine_tuned_llm # Free up memory
    torch.cuda.empty_cache()

    # --- Evaluate Base Model ---
    print("\n" + "="*50)
    print(f"--- INITIALIZING BASE MODEL: {BASE_MODEL} ---")
    print("="*50)
    base_llm = ChatOllama(model=BASE_MODEL)
    base_avg_score = evaluate_model(BASE_MODEL, base_llm, test_cases)
    results[BASE_MODEL] = base_avg_score
    del base_llm # Free up memory
    torch.cuda.empty_cache()

    # --- Final Results Summary ---
    print("\n\n" + "="*50)
    print("--- FINAL EVALUATION SUMMARY ---")
    print("="*50)

    ft_score = results.get(FINE_TUNED_MODEL, 0)
    base_score = results.get(BASE_MODEL, 0)

    print(f"\nFine-Tuned Model ({FINE_TUNED_MODEL}):")
    print(f"  - Average Score: {ft_score:.2f}/5")

    print(f"\nBase Model ({BASE_MODEL}):")
    print(f"  - Average Score: {base_score:.2f}/5")

    print("\n" + "="*50)

    improvement = ft_score - base_score
    if improvement > 0.2:
        print(f"\n🏆 The fine-tuned model shows a significant improvement of {improvement:.2f} points on average!")
    elif improvement > 0:
        print(f"\n✅ The fine-tuned model shows a slight improvement of {improvement:.2f} points on average.")
    else:
        print("\n📉 The fine-tuned model did not show a significant improvement over the base model.")

# --- Start the process ---
run_full_evaluation()
