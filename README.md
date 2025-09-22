# MedGraph Navigator: A Full-Stack Multi-Agent Healthcare Assistant

## About The Project

MedGraph Navigator is a sophisticated, full-stack healthcare assistant designed to provide users with intelligent, context-aware medical information and services. Built with a modern multi-agent architecture using **LangGraph**, this application leverages a combination of local, fine-tuned, and cloud-based Large Language Models (LLMs) to offer a seamless and powerful conversational experience.

The system can analyze symptoms, provide detailed information on health conditions, summarize medical reports from images, and find nearby doctors in real-time. The entire workflow is orchestrated by an intelligent routing agent that understands the user's conversational intent, making this project a complete end-to-end demonstration of advanced agentic AI.



---

## Built With

- **Frontend**: React, Vite
- **Backend**: Python, Flask
- **AI Orchestration**: LangChain, LangGraph
- **LLM Serving**: Ollama
- **Cloud APIs**: Google Gemini, Google Maps

---

## Core Features

- **Intelligent Multi-Agent System**: The backend is powered by a network of specialized AI agents that collaborate to handle complex tasks, orchestrated by a powerful router agent.
- **Advanced Symptom Analysis**: A fine-tuned language model provides accurate potential health issues based on user-described symptoms, using a hierarchical search for improved precision.
- **RAG-Based Q&A**: A Retrieval-Augmented Generation (RAG) agent answers follow-up questions by retrieving information from a dedicated medical knowledge base (`medquad.csv`).
- **Multimodal Medical Report Summarization**: Users can upload an image of a medical report (`.png`), which a vision-enabled agent (powered by Google's Gemini API) reads and passes to a summarizer agent for a structured, analytical summary.
- **Real-Time Doctor Finder**: A tool-using agent interfaces with the Google Maps API (via a local MCP server) to find real-world doctors and specialists based on the user's health issue and location.
- **Persistent Chat History**: The application saves every conversation, allowing users to browse, select, and continue previous sessions.
- **Modern & Responsive Frontend**: A clean, intuitive chat interface built with React, featuring a collapsible sidebar, chat history management, and a dedicated UI for file uploads.

---

## Technical Architecture

### Frontend

- **Framework**: React (Vite)
- **Styling**: Self-contained CSS within the `App.jsx` component for simplicity and portability.

### Backend

- **Framework**: Python with Flask & Flask-CORS
- **Orchestration**: LangGraph for building the stateful multi-agent workflow.
- **Core AI Library**: LangChain
- **AI & Models**:
    - **Local LLMs**: Ollama for serving text-based models like `llama3:8b` or the fine-tuned `monotykamary/medichat-llama3:8b`.
    - **Cloud LLMs**: Google's Gemini Flash API is used for the intelligent router and the vision-based data extraction.
    - **Model Fine-Tuning**: The core text model was fine-tuned on a medical symptom dataset using Google Colab and the Unsloth library for enhanced accuracy.
- **Data & Storage**:
    - **Chat History**: Stored as local JSON files in the `/backend/chats` directory.
    - **Knowledge Base**: A FAISS vector store is pre-processed from the `medquad.csv` for efficient similarity searches by the symptom agent.

---

## Project Structure

```
/MedGraph-Navigator/
|
|-- backend/
|   |-- chats/
|   |-- faiss_index/
|   |-- uploads/
|   |-- agent_symptom.py
|   |-- agent_rag.py
|   |-- agent_summarizer.py
|   |-- agent_extractor.py
|   |-- agent_finder.py
|   |-- app.py
|   |-- database.py
|   |-- main.py
|   |-- mcp_server.py
|   |-- preprocess.py
|   |-- requirements.txt
|   `-- .env
|
|-- data/
|   `-- medquad.csv
|
|-- frontend/
|   |-- public/
|   |-- src/
|   |   `-- App.jsx
|   |-- index.html
|   |-- package.json
|   `-- vite.config.js
|
|-- Tests/
|   |-- test_cases_category_1.json
|   |-- ...
|
`-- README.md
```

---

## Setup and Installation

### A. Backend Setup

1. **Navigate to the Backend Directory:**
    ```bash
    cd backend
    ```

2. **Create a Virtual Environment (Recommended):**
    ```bash
    py -3.10 -m venv .venv
    .venv\Scripts\activate
    ```

3. **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4. **Set Up API Keys:**
    - Create a file named `.env` inside the backend directory.
    - Add your API keys to this file:
        ```env
        GOOGLE_API_KEY="YOUR_GOOGLE_AI_API_KEY"
        GOOGLE_MAPS_API_KEY="YOUR_GOOGLE_MAPS_API_KEY"
        ```

5. **Run the Pre-processing Script:**  
   This creates the vector store from the `medquad.csv` file located in the data directory.
    ```bash
    python preprocess.py
    ```

6. **Set Up Ollama:**
    - Install and run the Ollama application.
    - Pull the necessary models:
        ```bash
        ollama pull monotykamary/medichat-llama3:8b
        ollama pull llama3:8b
        ```

### B. Frontend Setup

1. **Navigate to the Frontend Directory:**
    ```bash
    cd frontend
    ```

2. **Install Node Modules:**
    ```bash
    npm install
    ```

---

