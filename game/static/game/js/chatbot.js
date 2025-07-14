console.log("✅ chatbot.js loaded");


let hasShownWelcome = false;

function toggleZombiebot() {
    const chatbox = document.getElementById("zombiebot-chatbox");
    const isOpening = chatbox.classList.contains("hidden");

    chatbox.classList.toggle("hidden");

    // Show welcome message when opening chatbot for the first time
    if (isOpening && !hasShownWelcome) {
        showWelcomeMessage();
        hasShownWelcome = true;
    }
}

function showWelcomeMessage() {
    const welcomeMessage = `Hey there! 👋 I'm Zeebs, your friendly zombie chatbot assistant! 🧟‍♂️

I'm here to help you with any questions about SPOT-ify - whether it's about gameplay, scoring, features, or just want to chat!

Feel free to ask me anything! 🎵✨`;

    // Add a small delay to make it feel more natural
    setTimeout(() => {
        appendZombiebotMessage('bot', welcomeMessage);
    }, 500);
}

let isFirstMessage = true;

function showTypingIndicator() {
    const msgBox = document.getElementById('zombiebot-messages');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'text-left text-sm text-gray-400';
    typingDiv.id = 'zombiebot-typing';
    typingDiv.innerText = isFirstMessage ? 'Waking up Zeebs... 💤' : 'Zeebs is typing...';
    msgBox.appendChild(typingDiv);
    msgBox.scrollTop = msgBox.scrollHeight;
}

function removeTypingIndicator() {
    const typingDiv = document.getElementById('zombiebot-typing');
    if (typingDiv) typingDiv.remove();
}

function appendZombiebotMessage(sender, message) {
    const msgBox = document.getElementById('zombiebot-messages');

    // 👇 Replace UPI ID with clickable span if found
    if (message.includes('rvydeeskumar@oksbi')) {
        message = message.replace(
            'rvydeeskumar@oksbi',
            `<span onclick="copyToClipboard('rvydeeskumar@oksbi')" style="color:var(--neon-purple); font-weight:bold; cursor:pointer;">rvydeeskumar@oksbi</span>`
        );
    }

    const wrapper = document.createElement('div');
    wrapper.className = 'zb-msg-row';
    wrapper.style.justifyContent = sender === 'you' ? 'flex-end' : 'flex-start';

    const bubble = document.createElement('div');
    bubble.className = sender === 'you' ? 'zb-bubble-user' : 'zb-bubble-bot';

    // 👇 Use innerHTML instead of innerText so HTML formatting works
    bubble.innerHTML = message;

    wrapper.appendChild(bubble);
    msgBox.appendChild(wrapper);
    msgBox.scrollTop = msgBox.scrollHeight;
    bubble.scrollIntoView({ behavior: 'smooth' });
}




function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const trimmed = cookie.trim();
            if (trimmed.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(trimmed.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

async function sendZombiebotMessage() {
    const input = document.getElementById('zombiebot-input');
    const message = input.value.trim();
    if (!message) return;

    appendZombiebotMessage('you', message);
    input.value = '';
    showTypingIndicator();

    try {
        const response = await fetch(`/${window.currentLanguage || 'tamil'}/zombiebot/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie('csrftoken'),
            },
            body: JSON.stringify({ message }),
        });
        await new Promise(resolve => setTimeout(resolve, 800)); 
        const data = await response.json();
        removeTypingIndicator();
        appendZombiebotMessage('bot', data.reply);
        isFirstMessage = false;
    } catch (err) {
        removeTypingIndicator();
        appendZombiebotMessage('bot', "Zombiebot is taking a nap... 🧠💤");
        console.error("Error:", err);
    }
}

document.addEventListener('DOMContentLoaded', function () {
    const input = document.getElementById('zombiebot-input');
    input.addEventListener('keydown', function (event) {
        if (event.key === 'Enter') {
            event.preventDefault(); // prevent newline
            sendZombiebotMessage();
        }
    });
});

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        alert(`UPI ID copied: ${text}`);
    });
}





console.log("✅ Global functions registered");
window.toggleZombiebot = toggleZombiebot;
window.sendZombiebotMessage = sendZombiebotMessage;

