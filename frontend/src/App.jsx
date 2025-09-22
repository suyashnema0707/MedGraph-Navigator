import React, { useState, useEffect, useRef } from 'react';

// --- CSS STYLES ---
// This version uses a more robust Flexbox layout to ensure the sidebar and input are fixed.
const styles = `
  :root {
    --sidebar-bg: #f1f5f9; /* Light Slate */
    --chat-bg: #ffffff;    /* White */
    --user-bubble-bg: #3b82f6; /* Blue 500 */
    --ai-bubble-bg: #e5e7eb; /* Gray 200 */
    --text-light: #ffffff;
    --text-dark: #1f2937; /* Slate 800 */
    --accent-blue: #3b82f6;
    --accent-blue-hover: #2563eb;
    --icon-color: #6b7280; /* Gray 500 */
    --sidebar-hover-bg: #e5e7eb;
    --sidebar-active-bg: #d1d5db;
    --sidebar-border-color: #e5e7eb;
  }

  body {
    overflow: hidden; /* Prevent body scroll */
  }

  .app-container {
    display: flex;
    height: 100vh;
    width: 100vw;
    background-color: var(--chat-bg);
    font-family: 'Inter', sans-serif;
  }

  /* --- Sidebar Styles --- */
  .sidebar {
    background-color: var(--sidebar-bg);
    color: var(--text-dark);
    width: 16rem;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
    transition: width 0.3s ease-in-out, padding 0.3s ease-in-out;
    border-right: 2px solid var(--sidebar-border-color);
    flex-shrink: 0;
    height: 100vh;
  }
  .sidebar.hidden {
    width: 0;
    padding: 1rem 0;
    overflow: hidden;
  }

  @media (max-width: 767px) {
    .sidebar {
      position: absolute;
      z-index: 30;
      transition: transform 0.3s ease-in-out;
    }
    .sidebar.hidden {
        transform: translateX(-100%);
        width: 16rem; /* Restore width when hidden on mobile */
        padding: 1rem;
    }
  }

  .new-chat-btn {
    width: 100%;
    background-color: var(--accent-blue);
    border-radius: 0.5rem;
    padding: 0.75rem;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    color: var(--text-light);
    border: none;
    cursor: pointer;
    transition: background-color 0.2s;
    font-weight: 600;
  }
  .new-chat-btn:hover { background-color: var(--accent-blue-hover); }

  .history-container { flex-grow: 1; overflow-y: auto; }
  .history-title {
    font-size: 0.875rem;
    font-weight: 600;
    color: #6b7280;
    margin-bottom: 0.5rem;
    padding: 0 0.5rem;
  }
  .history-list {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }
  .history-item {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      border-radius: 0.5rem;
      transition: background-color 0.2s;
  }
  .history-item:hover { background-color: var(--sidebar-hover-bg); }
  .history-item.active { background-color: var(--sidebar-active-bg); }

  .history-item-btn {
    flex-grow: 1;
    text-align: left;
    padding: 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    background: none;
    border: none;
    color: var(--text-dark);
    cursor: pointer;
    overflow: hidden;
  }
  .history-item-btn span {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .delete-chat-btn {
      padding: 0.75rem;
      background: none;
      border: none;
      color: var(--icon-color);
      cursor: pointer;
      flex-shrink: 0;
  }
   .delete-chat-btn:hover { color: var(--text-dark); }

  .chat-interface {
    flex-grow: 1;
    display: flex;
    flex-direction: column;
    height: 100vh; /* Full height */
    overflow: hidden; /* Prevent this container from scrolling */
    background-color: var(--chat-bg);
  }

  .chat-header {
    padding: 0.5rem 1rem;
    border-bottom: 1px solid #e5e7eb;
    background-color: white;
    z-index: 10;
    flex-shrink: 0; /* Prevent header from shrinking */
  }
  .menu-btn {
    padding: 0.5rem;
    border-radius: 9999px;
    background: none;
    border: none;
    cursor: pointer;
    transition: background-color 0.2s;
    color: #6b7280;
  }
  .menu-btn:hover { background-color: #f3f4f6; }

  .chat-log {
    flex-grow: 1; /* Allow chat log to take up all available space */
    padding: 1.5rem;
    overflow-y: auto; /* THIS IS THE ONLY SCROLLABLE ELEMENT */
  }
  .message-container {
    display: flex;
    margin-bottom: 1rem;
    flex-direction: column;
    align-items: center;
  }
  .message-bubble {
    border-radius: 0.75rem;
    padding: 0.75rem 1rem;
    max-width: 80%;
    width: fit-content;
    line-height: 1.5;
    text-align: center;
  }
  .message-bubble.user { background-color: var(--user-bubble-bg); color: var(--text-light); align-self: center; }
  .message-bubble.ai, .message-bubble.loading { background-color: var(--ai-bubble-bg); color: var(--text-dark); align-self: center;}
  .message-bubble.loading {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  .dot-flashing {
    position: relative;
    width: 8px;
    height: 8px;
    border-radius: 5px;
    background-color: #9ca3af;
    color: #9ca3af;
    animation: dotFlashing 1s infinite linear alternate;
    animation-delay: .5s;
  }
  .dot-flashing::before, .dot-flashing::after {
    content: '';
    display: inline-block;
    position: absolute;
    top: 0;
  }
  .dot-flashing::before {
    left: -15px;
    width: 8px;
    height: 8px;
    border-radius: 5px;
    background-color: #9ca3af;
    color: #9ca3af;
    animation: dotFlashing 1s infinite alternate;
    animation-delay: 0s;
  }
  .dot-flashing::after {
    left: 15px;
    width: 8px;
    height: 8px;
    border-radius: 5px;
    background-color: #9ca3af;
    color: #9ca3af;
    animation: dotFlashing 1s infinite alternate;
    animation-delay: 1s;
  }
  @keyframes dotFlashing {
    0% { background-color: #9ca3af; }
    50%, 100% { background-color: #d1d5db; }
  }

  .structured-response-container {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
      width: 100%;
      max-width: 80%;
      align-items: center;
  }
  .structured-card {
      background-color: #f9fafb;
      border: 1px solid #e5e7eb;
      border-radius: 0.75rem;
      padding: 1rem;
      width: 100%;
      text-align: left;
      box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
  }
  .card-title {
      font-weight: 600;
      color: var(--text-dark);
      font-size: 1.125rem;
  }
  .card-address, .card-text {
      color: #4b5563;
      font-size: 0.875rem;
      margin-top: 0.25rem;
  }
  .card-rating {
      color: #f59e0b;
      font-weight: 600;
      margin-top: 0.5rem;
  }
  .card-section-title {
      font-weight: 600;
      color: var(--text-dark);
      margin-top: 1rem;
      margin-bottom: 0.5rem;
      font-size: 1rem;
      border-bottom: 1px solid #e5e7eb;
      padding-bottom: 0.25rem;
  }
  .card-list {
      list-style-type: disc;
      padding-left: 1.25rem;
      color: #4b5563;
  }
  .card-disclaimer {
      font-style: italic;
      color: #6b7280;
      font-size: 0.875rem;
      margin-top: 1rem;
  }

  .loading-indicator {
      display: flex;
      justify-content: center;
      align-items: center;
      padding: 2rem;
      color: #6b7280;
      font-style: italic;
  }

  .error-message {
      background-color: #fef2f2;
      border: 1px solid #fecaca;
      color: #dc2626;
      padding: 0.75rem;
      border-radius: 0.5rem;
      margin: 0.5rem 0;
      text-align: center;
  }

  .chat-input-area {
    padding: 1rem;
    border-top: 1px solid #e5e7eb;
    background-color: #ffffff;
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 10;
    flex-shrink: 0; /* Prevent input area from shrinking */
  }
  .chat-input-form {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background-color: #f3f4f6;
    border-radius: 9999px;
    padding: 0.5rem 0.75rem;
    border: 1px solid #e5e7eb;
    width: 80%;
    max-width: 720px;
    transition: box-shadow 0.2s;
  }
  .chat-input-form:focus-within {
      box-shadow: 0 0 0 2px var(--accent-blue);
  }

  .upload-btn {
    padding: 0.75rem;
    border-radius: 9999px;
    background: none;
    border: none;
    cursor: pointer;
    color: var(--icon-color);
    transition: background-color 0.2s;
  }
  .upload-btn:hover { background-color: #d1d5db; }

  .chat-input {
    flex-grow: 1;
    border: none;
    background: none;
    padding: 0.75rem 0.25rem;
    font-size: 1rem;
    resize: none;
    max-height: 120px;
    overflow-y: auto;
    text-align: center;
    color: var(--text-dark);
  }
  .chat-input:focus { outline: none; }

  .send-btn {
    padding: 0.75rem;
    background-color: var(--accent-blue);
    color: var(--text-light);
    border: none;
    border-radius: 0.5rem;
    cursor: pointer;
    transition: background-color 0.2s;
  }
  .send-btn:hover { background-color: var(--accent-blue-hover); }
  .send-btn:disabled {
    background-color: #9ca3af;
    cursor: not-allowed;
  }
`;

const Icon = ({ name }) => {
  const icons = {
    plus: ( <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14" /><path d="M12 5v14" /></svg> ),
    message: ( <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></svg> ),
    paperclip: ( <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.59a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg> ),
    send: ( <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></svg> ),
    trash: ( <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><path d="M10 11v6"/><path d="M14 11v6"/></svg> ),
    menu: ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="4" x2="20" y1="12" y2="12"/><line x1="4" x2="20" y1="6" y2="6"/><line x1="4" x2="20" y1="18" y2="18"/></svg> ),
    refresh: ( <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M3 21v-5h5"/></svg> )
  };
  return icons[name] || null;
};

const Sidebar = ({ chats, activeChatId, onNewChat, onSelectChat, onDeleteChat, onRefresh, isVisible, isLoading }) => {
  return (
    <div className={`sidebar ${isVisible ? '' : 'hidden'}`}>
      <button onClick={onNewChat} className="new-chat-btn" disabled={isLoading}>
        <Icon name="plus" />
        <span>New Chat</span>
      </button>
      <div className="history-container">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
          <h2 className="history-title">History</h2>
          <button
            onClick={onRefresh}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              color: '#6b7280',
              padding: '0.25rem'
            }}
            disabled={isLoading}
            title="Refresh chat list"
          >
            <Icon name="refresh" />
          </button>
        </div>
        <ul className="history-list">
          {chats.length === 0 ? (
            <li style={{ padding: '1rem', textAlign: 'center', color: '#6b7280', fontSize: '0.875rem' }}>
              No chat history found
            </li>
          ) : (
            chats.map(chat => (
              <li key={chat.id} className={`history-item ${activeChatId === chat.id ? 'active' : ''}`}>
                <button onClick={() => onSelectChat(chat.id)} className="history-item-btn" disabled={isLoading}>
                  <Icon name="message" />
                  <span>{chat.title}</span>
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    if (window.confirm('Are you sure you want to delete this chat?')) {
                      onDeleteChat(chat.id);
                    }
                  }}
                  className="delete-chat-btn"
                  aria-label="Delete chat"
                  disabled={isLoading}
                >
                    <Icon name="trash" />
                </button>
              </li>
            ))
          )}
        </ul>
      </div>
    </div>
  );
};

// --- Updated Components for Structured Data ---
const DoctorCard = ({ doctor }) => (
    <div className="structured-card">
        <div className="card-title">{doctor.name}</div>
        <div className="card-address">{doctor.address}</div>
        {doctor.rating && <div className="card-rating">⭐ {doctor.rating}</div>}
    </div>
);

const ReportSummary = ({ summary }) => (
    <div className="structured-card">
        <div className="card-section-title">Key Observations</div>
        <ul className="card-list">
            {summary.key_observations.map((item, i) => <li key={i}>{item}</li>)}
        </ul>
        <div className="card-section-title">Lab Analysis</div>
         <ul className="card-list">
            {summary.lab_analysis.map((item, i) => <li key={i}><strong>{item.metric}:</strong> {item.value} ({item.assessment})</li>)}
        </ul>
        <div className="card-section-title">Areas for Improvement</div>
        <ul className="card-list">
            {summary.areas_for_improvement.map((item, i) => <li key={i}>{item}</li>)}
        </ul>
        <div className="card-disclaimer">{summary.disclaimer}</div>
    </div>
);

const ChatMessage = ({ sender, text }) => {
    // Helper to safely parse JSON from a string
    const parseJson = (str, keys) => {
        if (typeof str !== 'string') return null;
        const match = str.match(/```json\s*(\{.*?\})\s*```/s);
        if (!match) return null;
        try {
            const parsed = JSON.parse(match[1]);
            // Check if all required keys are present
            if (keys.every(key => key in parsed)) {
                return parsed;
            }
            return null;
        } catch (e) {
            return null;
        }
    };

    const doctorsMatch = text.match(/```json\s*(\[.*?\])\s*```/s);
    let doctors = null;
    if (doctorsMatch) {
        try {
            doctors = JSON.parse(doctorsMatch[1]);
        } catch(e) { doctors = null; }
    }

    const summary = parseJson(text, ['key_observations', 'lab_analysis']);
    const introText = text.split('```json')[0].trim();

    if (sender === 'human' || sender === 'user') {
      return (
        <div className={`message-container`}>
          <div className={`message-bubble user`}>{text}</div>
        </div>
      );
    }

    if (sender === 'loading') {
      return (
        <div className={`message-container`}>
          <div className={`message-bubble loading`}>
            <div className="dot-flashing"></div>
          </div>
        </div>
      );
    }

    return (
        <div className={`message-container`}>
             {introText && <div className="message-bubble ai">{introText}</div>}
             {doctors && (
                <div className="structured-response-container">
                    {doctors.map((doc, index) => <DoctorCard key={index} doctor={doc} />)}
                </div>
             )}
             {summary && (
                <div className="structured-response-container">
                     <ReportSummary summary={summary} />
                </div>
             )}
        </div>
    );
};

const ChatInterface = ({ messages, onSendMessage, onFileUpload, onToggleSidebar, isSidebarVisible, isLoading }) => {
  const chatLogRef = useRef(null);
  const fileInputRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    if (chatLogRef.current) {
      chatLogRef.current.scrollTop = chatLogRef.current.scrollHeight;
    }
  }, [messages]);

  const handleFormSubmit = (e) => {
      e.preventDefault();
      const textarea = textareaRef.current;
      if (textarea && textarea.value.trim() && !isLoading) {
          onSendMessage(textarea.value);
          textarea.value = '';
          adjustTextareaHeight(textarea);
      }
  };

  const adjustTextareaHeight = (el) => {
    el.style.height = 'auto';
    el.style.height = (el.scrollHeight) + 'px';
  };

  const handleTextareaInput = (e) => {
    adjustTextareaHeight(e.target);
  };

  const handleUploadClick = () => {
    if (!isLoading) {
      fileInputRef.current.click();
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file && !isLoading) {
      onFileUpload(file);
    }
  };

  return (
    <div className={`chat-interface ${isSidebarVisible ? '' : 'sidebar-hidden'}`}>
      <div className="chat-header">
        <button onClick={onToggleSidebar} className="menu-btn" aria-label="Toggle sidebar">
            <Icon name="menu"/>
        </button>
      </div>
      <div ref={chatLogRef} className="chat-log">
        {messages.length === 0 ? (
          <div className="loading-indicator">
            No messages yet. Start a conversation!
          </div>
        ) : (
          messages.map((msg, index) => (
            <ChatMessage key={index} sender={msg.type} text={msg.content} />
          ))
        )}
      </div>
      <div className="chat-input-area">
        <form onSubmit={handleFormSubmit} className="chat-input-form">
          <button
            type="button"
            onClick={handleUploadClick}
            className="upload-btn"
            aria-label="Upload medical report"
            disabled={isLoading}
          >
            <Icon name="paperclip" />
          </button>
          <textarea
            ref={textareaRef}
            name="message"
            className="chat-input"
            placeholder={isLoading ? "Processing..." : "Describe your symptoms or ask a question..."}
            rows="1"
            onInput={handleTextareaInput}
            disabled={isLoading}
          ></textarea>
          <button
            type="submit"
            className="send-btn"
            aria-label="Send message"
            disabled={isLoading}
          >
             <Icon name="send" />
          </button>
        </form>
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          style={{ display: 'none' }}
          accept="image/*,.pdf,.txt"
          disabled={isLoading}
        />
      </div>
    </div>
  );
};

export default function App() {
  const [isSidebarVisible, setIsSidebarVisible] = useState(true);
  const [chats, setChats] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);
  const [error, setError] = useState(null);

  const API_URL = "http://127.0.0.1:5000";

  // Initialize app on component mount
  useEffect(() => {
    const initializeApp = async () => {
      console.log('🚀 Initializing app...');
      setIsLoading(true);

      try {
        const allChats = await fetchChats();
        if (allChats && allChats.length > 0) {
          console.log(`📚 Found ${allChats.length} existing chats, loading most recent...`);
          await handleSelectChat(allChats[0].id);
        } else {
          console.log('📝 No existing chats found, creating new chat...');
          await handleNewChat();
        }
      } catch (error) {
        console.error('❌ Failed to initialize app:', error);
        setError('Failed to load chat history. Please refresh the page.');
      } finally {
        setIsInitialized(true);
        setIsLoading(false);
      }
    };

    initializeApp();
  }, []);

  //Fetch all chats from backend
  const fetchChats = async () => {
    try {
      console.log('🔄 Fetching chats from backend...');
      const response = await fetch(`${API_URL}/get_chats`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('✅ Fetched chats successfully:', data);

      // Handle different response formats
      let chatsList = [];
      if (Array.isArray(data)) {
        chatsList = data;
      } else if (data.chats && Array.isArray(data.chats)) {
        chatsList = data.chats;
      } else if (data.data && Array.isArray(data.data)) {
        chatsList = data.data;
      }

      setChats(chatsList);
      setError(null);
      return chatsList;
    } catch (error) {
      console.error('❌ Error fetching chats:', error);
      setError('Failed to load chats. Please check your connection.');
      return [];
    }
  };

  // Create a new chat
  const handleNewChat = async () => {
    try {
      console.log('➕ Creating new chat...');
      const response = await fetch(`${API_URL}/new_chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('✅ New chat created:', data);

      const newChat = {
        id: data.session_id || data.id || Date.now().toString(),
        title: data.title || `New Chat ${new Date().toLocaleTimeString()}`
      };

      // Add the new chat to the top of the list
      setChats(prevChats => [newChat, ...prevChats]);
      setActiveChatId(newChat.id);
      setMessages([{ type: 'ai', content: 'Hello! How can I help you today?' }]);
      setError(null);

    } catch (error) {
      console.error('❌ Error starting new chat:', error);
      setError('Failed to create new chat. Creating temporary chat...');

      // Fallback: create a temporary chat ID
      const tempId = `temp_${Date.now()}`;
      const tempChat = {
        id: tempId,
        title: `New Chat ${new Date().toLocaleTimeString()}`
      };
      setChats(prevChats => [tempChat, ...prevChats]);
      setActiveChatId(tempId);
      setMessages([{ type: 'ai', content: 'Hello! How can I help you today? (Note: This is a temporary chat)' }]);
    }
  };

  // Select and load a specific chat
  const handleSelectChat = async (id) => {
    if (id === activeChatId) {
      console.log('🔄 Chat already active, skipping...');
      return;
    }

    console.log('📂 Selecting chat:', id);
    setActiveChatId(id);
    setIsLoading(true);

    try {
      const response = await fetch(`${API_URL}/get_chat_history/${id}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('✅ Chat history loaded:', data);

      // Handle different response formats from your backend
      let chatHistory = [];
      if (Array.isArray(data)) {
        chatHistory = data;
      } else if (data.messages && Array.isArray(data.messages)) {
        chatHistory = data.messages;
      } else if (data.history && Array.isArray(data.history)) {
        chatHistory = data.history;
      } else if (data.data && Array.isArray(data.data)) {
        chatHistory = data.data;
      }

      // If no history, start with greeting
      if (chatHistory.length === 0) {
        chatHistory = [{ type: 'ai', content: 'Hello! How can I help you today?' }];
      }

      setMessages(chatHistory);
      setError(null);

    } catch (error) {
      console.error(`❌ Error fetching history for chat ${id}:`, error);
      setError('Failed to load chat history.');
      // Fallback to greeting message
      setMessages([{ type: 'ai', content: 'Hello! How can I help you today?' }]);
    } finally {
      setIsLoading(false);
    }
  };

  // Delete a chat
  const handleDeleteChat = async (idToDelete) => {
    try {
      console.log('🗑️ Deleting chat:', idToDelete);

      // Send delete request to backend
      const response = await fetch(`${API_URL}/delete_chat/${idToDelete}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      console.log(`✅ Chat ${idToDelete} deleted successfully`);

      // Update local state
      const newChats = chats.filter(chat => chat.id !== idToDelete);
      setChats(newChats);

      if (activeChatId === idToDelete) {
        if (newChats.length > 0) {
          await handleSelectChat(newChats[0].id);
        } else {
          await handleNewChat();
        }
      }

      setError(null);

    } catch (error) {
      console.error(`❌ Error deleting chat ${idToDelete}:`, error);
      setError('Failed to delete chat from server, but removing from list...');

      // If backend delete fails, still update UI
      const newChats = chats.filter(chat => chat.id !== idToDelete);
      setChats(newChats);

      if (activeChatId === idToDelete) {
        if (newChats.length > 0) {
          await handleSelectChat(newChats[0].id);
        } else {
          await handleNewChat();
        }
      }
    }
  };

  // Send a message
  const handleSendMessage = async (message) => {
    if (!activeChatId) {
      console.error('❌ No active chat ID');
      setError('No active chat. Please create a new chat.');
      return;
    }

    console.log('💬 Sending message:', message);

    const userMessage = { type: 'human', content: message };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: message,
          session_id: activeChatId
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('✅ Chat response received:', data);

      const aiMessage = {
        type: 'ai',
        content: data.response || data.message || 'Sorry, I received an empty response.'
      };
      setMessages([...newMessages, aiMessage]);

      // Refresh chat list in case the title changed
      setTimeout(() => fetchChats(), 500);

    } catch (error) {
      console.error('❌ Chat error:', error);
      setError('Failed to send message. Please try again.');
      const errorMessage = {
        type: 'ai',
        content: "Sorry, I'm having trouble connecting. Please try again."
      };
      setMessages([...newMessages, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Upload a file
  const handleFileUpload = async (file) => {
    if (!activeChatId) {
      console.error('❌ No active chat ID');
      setError('No active chat. Please create a new chat.');
      return;
    }

    console.log('📎 Uploading file:', file.name);

    const userMessage = { type: 'human', content: `Uploaded file: ${file.name}` };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setIsLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('report_image', file);
    formData.append('session_id', activeChatId);

    try {
      const response = await fetch(`${API_URL}/upload_report`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('✅ Upload response received:', data);

      const aiMessage = {
        type: 'ai',
        content: data.response || data.message || 'File uploaded successfully.'
      };
      setMessages([...newMessages, aiMessage]);

      // Refresh chat list to update title
      setTimeout(() => fetchChats(), 500);

    } catch (error) {
      console.error('❌ Upload error:', error);
      setError('Failed to upload file. Please try again.');
      const errorMessage = {
        type: 'ai',
        content: "An error occurred while uploading the report. Please try again."
      };
      setMessages([...newMessages, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Refresh chat list
  const handleRefreshChats = async () => {
    console.log('🔄 Refreshing chat list...');
    await fetchChats();
  };

  // Toggle sidebar
  const toggleSidebar = () => {
    setIsSidebarVisible(!isSidebarVisible);
  };

  // Prepare messages for display (add loading indicator if needed)
  const displayMessages = isLoading
    ? [...messages, { type: 'loading', content: '...' }]
    : messages;

  // Show loading screen during initialization
  if (!isInitialized) {
    return (
      <>
        <style>{styles}</style>
        <div className="app-container">
          <div className="loading-indicator">
            <div className="dot-flashing"></div>
            <span style={{ marginLeft: '1rem' }}>Loading chat application...</span>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <style>{styles}</style>
      <div className="app-container">
        {error && (
          <div className="error-message">
            {error}
            <button
              onClick={() => setError(null)}
              style={{
                marginLeft: '0.5rem',
                background: 'none',
                border: 'none',
                color: '#dc2626',
                cursor: 'pointer',
                fontWeight: 'bold'
              }}
            >
              ×
            </button>
          </div>
        )}

        <Sidebar
          chats={chats}
          activeChatId={activeChatId}
          onNewChat={handleNewChat}
          onSelectChat={handleSelectChat}
          onDeleteChat={handleDeleteChat}
          onRefresh={handleRefreshChats}
          isVisible={isSidebarVisible}
          isLoading={isLoading}
        />

        <ChatInterface
          messages={displayMessages}
          onSendMessage={handleSendMessage}
          onFileUpload={handleFileUpload}
          onToggleSidebar={toggleSidebar}
          isSidebarVisible={isSidebarVisible}
          isLoading={isLoading}
        />
      </div>
    </>
  );
}