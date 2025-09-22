# File: database.py

import os
import json
import uuid
from langchain_core.messages import AIMessage, HumanMessage

# Create a directory to store chat histories if it doesn't exist
CHAT_HISTORY_DIR = "chats"
if not os.path.exists(CHAT_HISTORY_DIR):
    os.makedirs(CHAT_HISTORY_DIR)


def get_new_session_id():
    """Generates a new unique session ID."""
    return str(uuid.uuid4())


def message_to_dict(message):
    """Converts a LangChain message object to a serializable dictionary."""
    if isinstance(message, HumanMessage):
        return {"type": "human", "content": message.content}
    if isinstance(message, AIMessage):
        return {"type": "ai", "content": message.content}
    return {"type": "system", "content": str(message)}


def dict_to_message(d):
    """Converts a dictionary back into a LangChain message object."""
    if d.get("type") == "human":
        return HumanMessage(content=d.get("content", ""))
    if d.get("type") == "ai":
        return AIMessage(content=d.get("content", ""))
    return d


def save_chat_state(session_id: str, state: dict):
    """Saves the entire application state to a JSON file."""
    file_path = os.path.join(CHAT_HISTORY_DIR, f"{session_id}.json")
    serializable_state = state.copy()
    serializable_state['messages'] = [message_to_dict(m) for m in state.get('messages', [])]

    # Add metadata for better chat management
    if 'session_id' not in serializable_state:
        serializable_state['session_id'] = session_id
    if 'created_at' not in serializable_state:
        serializable_state['created_at'] = str(uuid.uuid1().time)
    if 'updated_at' not in serializable_state:
        serializable_state['updated_at'] = str(uuid.uuid1().time)

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(serializable_state, f, ensure_ascii=False, indent=4)


def load_chat_state(session_id: str) -> dict:
    """Loads the entire application state from a JSON file."""
    file_path = os.path.join(CHAT_HISTORY_DIR, f"{session_id}.json")
    if not os.path.exists(file_path):
        return {"messages": [], "health_issue": "", "extracted_text": "", "image_path": ""}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            serializable_state = json.load(f)
            serializable_state['messages'] = [dict_to_message(d) for d in serializable_state.get('messages', [])]
            return serializable_state
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error loading chat state for {session_id}: {e}")
        return {"messages": [], "health_issue": "", "extracted_text": "", "image_path": ""}


def load_raw_chat_data(session_id: str) -> dict:
    """Loads the raw JSON data without converting to LangChain objects."""
    file_path = os.path.join(CHAT_HISTORY_DIR, f"{session_id}.json")
    if not os.path.exists(file_path):
        return {"messages": [], "health_issue": "", "extracted_text": "", "image_path": ""}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error loading raw chat data for {session_id}: {e}")
        return {"messages": [], "health_issue": "", "extracted_text": "", "image_path": ""}


def get_all_chats():
    """Scans the chat directory and returns a list of chat summaries."""
    chats = []
    if not os.path.exists(CHAT_HISTORY_DIR):
        return []

    try:
        files = sorted(
            [os.path.join(CHAT_HISTORY_DIR, f) for f in os.listdir(CHAT_HISTORY_DIR) if f.endswith('.json')],
            key=os.path.getmtime,
            reverse=True
        )

        for file_path in files:
            try:
                session_id = os.path.basename(file_path).replace(".json", "")

                # Use raw data instead of converted LangChain objects
                chat_data = load_raw_chat_data(session_id)

                # Generate title from first human message
                title = "New Conversation"
                messages = chat_data.get("messages", [])

                if messages:
                    # Find first human message
                    first_user_message = None
                    for msg in messages:
                        if isinstance(msg, dict) and msg.get("type") == "human":
                            first_user_message = msg.get("content", "")
                            break

                    if first_user_message:
                        # Clean up the title
                        if first_user_message.startswith("Uploaded file:"):
                            title = "Medical Report Analysis"
                        else:
                            title = first_user_message[:35] + '...' if len(
                                first_user_message) > 35 else first_user_message

                chats.append({
                    "id": session_id,
                    "title": title
                })

            except Exception as e:
                print(f"Error processing chat file {file_path}: {e}")
                continue

    except Exception as e:
        print(f"Error reading chat histories: {e}")

    return chats


def get_chat_history_for_frontend(session_id: str):
    """Gets chat history in format suitable for frontend display."""
    chat_data = load_raw_chat_data(session_id)
    messages = chat_data.get("messages", [])

    # Ensure messages are in the correct format for frontend
    formatted_messages = []
    for msg in messages:
        if isinstance(msg, dict):
            formatted_messages.append({
                "type": msg.get("type", "system"),
                "content": msg.get("content", "")
            })

    return formatted_messages


def delete_chat_file(session_id: str):
    """Deletes the JSON file for a given session ID."""
    file_path = os.path.join(CHAT_HISTORY_DIR, f"{session_id}.json")
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Successfully deleted chat file: {session_id}.json")
            return True
        else:
            print(f"Chat file not found: {session_id}.json")
            return False
    except Exception as e:
        print(f"Error deleting chat file {session_id}.json: {e}")
        return False


def create_new_chat(title="New Conversation"):
    """Creates a new chat with initial state."""
    session_id = get_new_session_id()
    initial_state = {
        "session_id": session_id,
        "messages": [],
        "health_issue": "",
        "extracted_text": "",
        "image_path": "",
        "title": title,
        "created_at": str(uuid.uuid1().time),
        "updated_at": str(uuid.uuid1().time)
    }
    save_chat_state(session_id, initial_state)
    return session_id, title