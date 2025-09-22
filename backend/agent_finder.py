# File: agent_finder.py

import os
import json
import re
import requests
from typing import TypedDict, Annotated
from langchain_core.messages import AIMessage, HumanMessage
from langchain_ollama import ChatOllama


# --- State Definition ---
class AppState(TypedDict):
    messages: Annotated[list, lambda x, y: x + y]
    health_issue: str


# --- Doctor Finder Agent with Improved State-Aware Logic ---
class DoctorFinderAgent:
    def __init__(self, model: ChatOllama):
        self.model = model

    def find_nearby_doctors(self, specialty: str, location: str) -> str:
        """Calls the local MCP server to find doctors."""
        print(f"---Tool Executing (Finder Agent)---: Calling local MCP server for '{specialty}' in '{location}'")
        try:
            # This URL must exactly match the route and port in mcp_server.py
            response = requests.post(
                "http://127.0.0.1:5001/find_doctors",
                json={"specialty": specialty, "location": location},
                timeout=15
            )
            response.raise_for_status()
            return json.dumps(response.json())
        except requests.exceptions.RequestException as e:
            print(f"---Tool Error---: Could not connect to MCP server: {e}")
            return json.dumps({"error": f"Failed to connect to the doctor finder service: {e}"})

    def __call__(self, state: AppState):
        print("---AGENT 4: Doctor Finder---")

        history = state.get("messages", [])
        health_issue = state.get("health_issue", "")

        conversation_history = "\n".join([f"{msg.type}: {msg.content}" for msg in history])

        parsing_prompt = f"""You are an intelligent assistant. Your task is to extract the medical specialty and location from a user's request.

        The user has already been diagnosed with the following potential issue: "{health_issue}"
        Use this as the medical specialty unless the user specifies a different one in their latest message.

        Here is the full conversation history for context:
        {conversation_history}

        Analyze the LAST user message to find the location.

        Respond with ONLY a JSON object containing the "specialty" and "location", enclosed in markdown code fences.
        For example:
        ```json
        {{"specialty": "Cardiology", "location": "Bhopal, India"}}
        ```
        If you cannot find a clear location, return:
        ```json
        {{"specialty": null, "location": null}}
        ```
        """

        try:
            response_str = self.model.invoke(parsing_prompt).content

            match = re.search(r"```json\s*(\{.*?\})\s*```", response_str, re.DOTALL)
            if not match:
                match = re.search(r'(\{.*?\})', response_str, re.DOTALL)
                if not match:
                    raise json.JSONDecodeError("No JSON object found in LLM response", response_str, 0)

            json_str = match.group(1)
            parsed_info = json.loads(json_str)

            specialty = parsed_info.get("specialty")
            location = parsed_info.get("location")

            if not specialty or not location:
                clarification_message = "I can help with that. To find the right doctor, could you please provide your current city or area?"
                return {"messages": [AIMessage(content=clarification_message)]}

        except (json.JSONDecodeError, AttributeError) as e:
            print(f"Error parsing LLM response for finder: {e}")
            clarification_message = "I had trouble understanding the request. Could you please rephrase it to include both a medical issue and a specific location?"
            return {"messages": [AIMessage(content=clarification_message)]}

        doctors_json = self.find_nearby_doctors(specialty, location)
        doctors_data = json.loads(doctors_json)

        if "error" in doctors_data:
            response_text = "I'm sorry, I encountered an error while searching for doctors. Please try again later."
        elif not doctors_data:
            response_text = f"I couldn't find any doctors specializing in '{specialty}' near '{location}'. You could try a broader search, like 'General Physician'."
        else:
            response_text = "Here are the doctor details I found:"
            doctors_json_string = json.dumps(doctors_data, indent=2)
            final_response = f"{response_text}\n```json\n{doctors_json_string}\n```"
            return {"messages": [AIMessage(content=final_response)]}

        return {"messages": [AIMessage(content=response_text)]}

