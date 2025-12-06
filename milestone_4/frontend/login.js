// ==========================================
// LOGIN PAGE LOGIC
// ==========================================

// API Configuration
const API_URL = "http://127.0.0.1:8000/api/auth";

// ==========================================
// VIEW TOGGLE
// ==========================================
function toggleView() {
    const login = document.getElementById('loginView');
    const signup = document.getElementById('signupView');
    
    if (login.style.display === 'none') {
        login.style.display = 'block';
        signup.style.display = 'none';
    } else {
        login.style.display = 'none';
        signup.style.display = 'block';
    }
    
    // Clear errors and inputs
    document.querySelectorAll('.error-msg').forEach(el => el.style.display = 'none');
    document.querySelectorAll('input').forEach(el => el.value = '');
}

// ==========================================
// AUTHENTICATION HANDLER
// ==========================================
async function handleAuth(endpoint, username, password, errorElementId) {
    const errorEl = document.getElementById(errorElementId);
    errorEl.style.display = 'none';

    try {
        const res = await fetch(`${API_URL}/${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const data = await res.json();
        
        if (res.ok) {
            return data;
        } else {
            throw new Error(data.detail || "Authentication failed");
        }
    } catch (err) {
        errorEl.innerText = err.message;
        errorEl.style.display = 'block';
        throw err;
    }
}

// ==========================================
// LOGIN HANDLER
// ==========================================
async function handleLogin() {
    const user = document.getElementById('loginUser').value;
    const pass = document.getElementById('loginPass').value;

    try {
        const data = await handleAuth('login', user, pass, 'loginError');
        localStorage.setItem('stockUser', data.username);
        window.location.href = 'index.html';
    } catch (e) {
        // Error handled in handleAuth
    }
}

// ==========================================
// SIGNUP HANDLER
// ==========================================
async function handleSignup() {
    const user = document.getElementById('signupUser').value;
    const pass = document.getElementById('signupPass').value;

    try {
        await handleAuth('signup', user, pass, 'signupError');
        alert("Account created successfully! Please sign in.");
        toggleView();
    } catch (e) {
        // Error handled in handleAuth
    }
}