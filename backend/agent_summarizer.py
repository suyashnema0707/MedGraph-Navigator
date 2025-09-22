# File: agent_summarizer.py

import json
import re
from typing import TypedDict, Annotated
from langchain_core.messages import AIMessage, HumanMessage
from langchain_ollama import ChatOllama


# --- State Definition ---
class AppState(TypedDict):
    messages: Annotated[list, lambda x, y: x + y]
    extracted_text: str


# --- Medical Report Summarizer Agent ---
class MedicalReportSummarizerAgent:
    def __init__(self, model: ChatOllama):
        self.model = model
        self.system_prompt = """You are an expert AI medical analyst. Your task is to analyze the provided medical report text and return a structured JSON summary.

        The JSON object must have the following keys: "key_observations", "lab_analysis", "areas_for_improvement", "disclaimer".

        - **key_observations**: A list of strings summarizing the key points from the doctor's narrative notes or impression.
        - **lab_analysis**: A list of objects, where each object has "metric", "value", and "assessment" keys. Compare each lab value against the provided healthy ranges.
        - **areas_for_improvement**: A list of strings containing general, actionable advice based on the analysis.
        - **disclaimer**: A standard safety disclaimer.

        **Healthy Ranges for Lab Values:**
        - Blood Pressure: < 120/80 mmHg
        - Total Cholesterol: < 200 mg/dL
        - LDL Cholesterol: < 100 mg/dL
        - HDL Cholesterol: > 60 mg/dL
        - Triglycerides: < 150 mg/dL
        - Hemoglobin A1c: < 5.7 %
        - WBC: 4.5 - 11.0 x10^9/L
        - Hemoglobin: 13.5-17.5 g/dL (male), 12.0-15.5 g/dL (female)

        Respond with ONLY the JSON object, enclosed in markdown code fences (```json ... ```).
        """

    def __call__(self, state: AppState):
        print("---AGENT 3: Medical Report Summarizer---")

        report_text = state.get("extracted_text")
        if not report_text:
            return {"messages": [AIMessage(content="There was no report text to summarize. Please provide a report.")]}

        # The user message is the extracted text from the previous step
        messages_for_llm = [
            HumanMessage(content=self.system_prompt),
            HumanMessage(content=f"Here is the medical report to analyze:\n\n{report_text}")
        ]

        try:
            response = self.model.invoke(messages_for_llm)

            # More robust parsing to find the JSON block
            match = re.search(r"```json\s*(\{.*?\})\s*```", response.content, re.DOTALL)
            if not match:
                # Fallback if markdown fences are missing
                match = re.search(r'(\{.*?\})', response.content, re.DOTALL)
                if not match:
                    raise json.JSONDecodeError("No JSON object found in LLM response", response.content, 0)

            json_str = match.group(1)

            # The agent's final output is the clean JSON string for the frontend
            final_response = f"Here is the summary of the report:\n```json\n{json_str}\n```"

            return {"messages": [AIMessage(content=final_response)]}

        except Exception as e:
            print(f"Error during summarization: {e}")
            error_message = "I'm sorry, I encountered an error while summarizing the report. The format of the report might be unusual. Please try again."
            return {"messages": [AIMessage(content=error_message)]}
