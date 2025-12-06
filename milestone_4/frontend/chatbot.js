const API_CHAT_URL = "http://127.0.0.1:8000/api/chat";

const chatWindow = document.getElementById('chatWindow');
const userInput = document.getElementById('userInput');

// Auto-focus input on load
window.onload = () => {
    userInput.focus();
};

// Logout Logic
document.querySelector('.logout-btn').addEventListener('click', () => {
    localStorage.removeItem('stockUser');
    window.location.href = 'login.html';
});

// Handle Enter Key
userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

async function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;

    // 1. Add User Message
    addMessage(text, 'user');
    userInput.value = '';
    
    // 2. Show Typing Indicator (Visual fake)
    const typingId = showTypingIndicator();
    scrollToBottom();

    try {
        // 3. Call Backend
        const response = await fetch(API_CHAT_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: text })
        });

        const data = await response.json();
        
        // Remove typing indicator
        removeTypingIndicator(typingId);
        
        // 4. Add Bot Response
        if (response.ok) {
            addMessage(data.response, 'bot');
        } else {
            addMessage("Sorry, I encountered an error connecting to the server.", 'bot');
        }

    } catch (error) {
        removeTypingIndicator(typingId);
        console.error(error);
        addMessage("Network error. Please try again later.", 'bot');
    }
    
    scrollToBottom();
}

function addMessage(text, sender) {
    const div = document.createElement('div');
    div.className = `message ${sender}`;
    
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    div.innerHTML = `
        <div class="bubble">${text}</div>
        <div class="timestamp">${time}</div>
    `;
    
    chatWindow.appendChild(div);
}

function showTypingIndicator() {
    const id = 'typing-' + Date.now();
    const div = document.createElement('div');
    div.id = id;
    div.className = 'message bot';
    div.innerHTML = `
        <div class="bubble" style="color: #888; font-style: italic;">
            AI is typing...
        </div>
    `;
    chatWindow.appendChild(div);
    return id;
}

function removeTypingIndicator(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function scrollToBottom() {
    chatWindow.scrollTop = chatWindow.scrollHeight;
}