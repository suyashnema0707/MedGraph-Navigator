# File: preprocess.py
# This script creates a SINGLE, unified vector store with metadata.
# Run this file once before running the main application.

import pandas as pd
import pickle
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings


def create_and_save_vector_store(file_path: str, output_path: str):
    """
    Reads a CSV, creates a single FAISS vector store for all documents,
    and saves it to a file. The 'focus_area' is stored as metadata.
    """
    print("--- Starting Pre-processing ---")
    print("This may still take some time, but it is much more memory-efficient.")

    try:
        # Initialize the embedding model
        print("Initializing embedding model...")
        embedding_model = OllamaEmbeddings(model="nomic-embed-text")

        # Load the dataset
        print(f"Loading data from {file_path}...")
        df = pd.read_csv(file_path)
        if 'question' not in df.columns or 'answer' not in df.columns or 'focus_area' not in df.columns:
            raise ValueError("CSV must contain 'question', 'answer', and 'focus_area' columns.")

        # --- FIX: Clean the data by dropping rows with missing values ---
        # This prevents the ValidationError by ensuring all data is valid before processing.
        print(f"Original number of rows: {len(df)}")
        df.dropna(subset=['question', 'answer', 'focus_area'], inplace=True)
        print(f"Number of rows after cleaning: {len(df)}")

        # Create LangChain Document objects with metadata
        print(f"Creating {len(df)} documents with metadata...")
        docs = [
            Document(
                page_content=row["answer"],
                metadata={"focus_area": row["focus_area"], "question": row["question"]}
            )
            for _, row in df.iterrows()
        ]

        # Create a single FAISS vector store from all documents
        print("Creating the unified FAISS vector store...")
        vector_store = FAISS.from_documents(docs, embedding_model)

        # Save the single vector store to a file
        print(f"Saving the vector store to {output_path}...")
        vector_store.save_local(output_path)

        print("--- Pre-processing Complete! ---")
        print(f"You can now run your main.py file.")

    except Exception as e:
        print(f"An error occurred during pre-processing: {e}")


if __name__ == '__main__':
    # The output path is now a folder name for the FAISS index
    create_and_save_vector_store(file_path="medquad.csv", output_path="faiss_index")
