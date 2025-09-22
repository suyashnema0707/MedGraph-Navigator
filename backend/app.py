# File: app.py

import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Import the main LangGraph app instance and necessary classes
from main import app as langgraph_app
from database import (
    get_new_session_id, save_chat_state, load_chat_state,
    get_all_chats, message_to_dict, delete_chat_file
)
from langchain_core.messages import HumanMessage

# --- Basic Setup ---
load_dotenv()
app = Flask(__name__)
# Allow requests from your React frontend's origin (e.g., http://localhost:5173 or any origin)
CORS(app, resources={r"/*": {"origins": "*"}})

# --- File Upload Configuration ---
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# --- Backend API Endpoints (Updated to match frontend expectations) ---

@app.route('/new_chat', methods=['POST'])
def new_chat_endpoint():
    """Creates a new chat session and returns its ID and a default title."""
    try:
        session_id = get_new_session_id()
        initial_state = {"messages": [], "health_issue": "", "extracted_text": "", "image_path": ""}
        save_chat_state(session_id, initial_state)
        new_chat_info = {"id": session_id, "title": "New Conversation"}
        return jsonify(new_chat_info)
    except Exception as e:
        print(f"Error in new_chat: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/get_chats', methods=['GET'])
def get_chats_endpoint():
    """Returns a list of all saved chat sessions."""
    try:
        chats = get_all_chats()
        return jsonify(chats)
    except Exception as e:
        print(f"Error in get_chats: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/get_chat_history/<session_id>', methods=['GET'])
def get_chat_history_endpoint(session_id):
    """Returns the full message history for a given chat session."""
    try:
        state = load_chat_state(session_id)
        serializable_messages = [message_to_dict(m) for m in state.get('messages', [])]
        return jsonify(serializable_messages)
    except Exception as e:
        print(f"Error getting chat history for {session_id}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/delete_chat/<session_id>', methods=['DELETE'])
def delete_chat_endpoint(session_id):
    """Deletes the file for a given chat session."""
    try:
        success = delete_chat_file(session_id)
        if success:
            return jsonify({"success": True, "message": f"Chat {session_id} deleted"}), 200
        else:
            return jsonify({"success": False, "message": "Chat not found"}), 404
    except Exception as e:
        print(f"Error deleting chat {session_id}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/chat', methods=['POST'])
def chat_endpoint():
    """Handles incoming text messages for a specific session."""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        user_message_content = data.get('message')

        if not session_id or not user_message_content:
            return jsonify({"error": "Session ID and message are required."}), 400

        current_state = load_chat_state(session_id)

        current_state['messages'].append(HumanMessage(content=user_message_content))
        current_state['image_path'] = ""  # Clear image path for text messages

        result_state = langgraph_app.invoke(current_state)
        save_chat_state(session_id, result_state)

        ai_response_obj = result_state['messages'][-1]
        ai_response_text = ai_response_obj.content if hasattr(ai_response_obj, 'content') else str(ai_response_obj)

        return jsonify({"response": ai_response_text})
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/upload_report', methods=['POST'])
def upload_report_endpoint():
    """Handles medical report image uploads."""
    try:
        session_id = request.form.get('session_id')
        if not session_id or 'report_image' not in request.files:
            return jsonify({"error": "Session ID and file are required."}), 400

        file = request.files['report_image']
        if file.filename == '' or not allowed_file(file.filename):
            return jsonify({"error": "Invalid file."}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        current_state = load_chat_state(session_id)

        # --- FIX: Reset state for a clean upload process ---
        current_state['image_path'] = filepath
        current_state['extracted_text'] = ""  # Clear any old extracted text

        current_state['messages'].append(HumanMessage(content=f"User uploaded an image: {filename}"))

        result_state = langgraph_app.invoke(current_state)
        save_chat_state(session_id, result_state)

        ai_response_obj = result_state['messages'][-1]
        ai_response_text = ai_response_obj.content if hasattr(ai_response_obj, 'content') else str(ai_response_obj)

        return jsonify({"response": ai_response_text})
    except Exception as e:
        print(f"Error in upload_report endpoint: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)

