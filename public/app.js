let myUserId = null;
let activePeerId = null;
let ws = null;

// Map<peerId, { isOnline: boolean, messages: Array }>
const conversations = new Map();

// DOM elements
const myUserIdEl = document.getElementById('myUserId');
const copyIdBtn = document.getElementById('copyIdBtn');
const regenIdBtn = document.getElementById('regenIdBtn');
const peerInput = document.getElementById('peerInput');
const startChatBtn = document.getElementById('startChatBtn');
const inputError = document.getElementById('inputError');
const contactsList = document.getElementById('contactsList');

const noChatSelected = document.getElementById('noChatSelected');
const activeChatView = document.getElementById('activeChatView');
const activePeerIdEl = document.getElementById('activePeerId');
const peerStatusBadge = document.getElementById('peerStatusBadge');
const messagesContainer = document.getElementById('messagesContainer');
const messageForm = document.getElementById('messageForm');
const messageInput = document.getElementById('messageInput');

// Initialize
init();

async function init() {
  await setupUserIdentity();
  connectWebSocket();
  setupEventListeners();
}

// 1. Get or Generate 8-digit User ID
async function setupUserIdentity() {
  let storedId = localStorage.getItem('messenger_8digit_id');
  if (!storedId || !/^\d{8}$/.test(storedId)) {
    try {
      const res = await fetch('/api/generate-id');
      const data = await res.json();
      storedId = data.userId;
      localStorage.setItem('messenger_8digit_id', storedId);
    } catch (err) {
      console.error('Failed to generate 8-digit ID:', err);
      storedId = Math.floor(10000000 + Math.random() * 90000000).toString();
      localStorage.setItem('messenger_8digit_id', storedId);
    }
  }

  myUserId = storedId;
  myUserIdEl.textContent = myUserId;
}

// 2. Connect WebSocket
function connectWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}`;

  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    // Register user ID on socket server
    ws.send(JSON.stringify({
      type: 'register',
      userId: myUserId
    }));
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      handleServerMessage(data);
    } catch (err) {
      console.error('Error parsing WS message:', err);
    }
  };

  ws.onclose = () => {
    console.log('WS disconnected. Reconnecting in 3 seconds...');
    setTimeout(connectWebSocket, 3000);
  };

  ws.onerror = (err) => {
    console.error('WS error:', err);
  };
}

// 3. Handle incoming WS messages
function handleServerMessage(data) {
  switch (data.type) {
    case 'registered':
      // data.onlineUsers contains currently online user IDs
      if (data.onlineUsers && Array.isArray(data.onlineUsers)) {
        data.onlineUsers.forEach(peerId => {
          getOrCreateConversation(peerId).isOnline = true;
        });
        renderContactsList();
      }
      break;

    case 'user_status':
      const { userId, isOnline } = data;
      if (userId !== myUserId) {
        const conv = getOrCreateConversation(userId);
        conv.isOnline = isOnline;
        if (activePeerId === userId) {
          updatePeerStatusBadge(isOnline);
        }
        renderContactsList();
      }
      break;

    case 'new_message': {
      const { message } = data;
      const peerId = message.senderId === myUserId ? message.recipientId : message.senderId;
      const conv = getOrCreateConversation(peerId);
      conv.messages.push(message);

      if (activePeerId === peerId) {
        appendMessage(message, false);
      }
      renderContactsList();
      break;
    }

    case 'message_sent': {
      const { message } = data;
      const peerId = message.recipientId;
      const conv = getOrCreateConversation(peerId);
      conv.messages.push(message);

      if (activePeerId === peerId) {
        appendMessage(message, true);
      }
      renderContactsList();
      break;
    }

    case 'error':
      showInputError(data.message);
      break;

    default:
      console.log('Unhandled message:', data);
  }
}

// Get or initialize conversation object
function getOrCreateConversation(peerId) {
  if (!conversations.has(peerId)) {
    conversations.set(peerId, {
      isOnline: false,
      messages: []
    });
  }
  return conversations.get(peerId);
}

// 4. Setup DOM Event Listeners
function setupEventListeners() {
  // Copy ID
  copyIdBtn.addEventListener('click', () => {
    navigator.clipboard.writeText(myUserId);
    const origText = copyIdBtn.textContent;
    copyIdBtn.textContent = '✓';
    setTimeout(() => copyIdBtn.textContent = origText, 1500);
  });

  // Regenerate ID
  regenIdBtn.addEventListener('click', async () => {
    localStorage.removeItem('messenger_8digit_id');
    location.reload();
  });

  // Start chat button
  startChatBtn.addEventListener('click', () => {
    handleStartChat();
  });

  peerInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      handleStartChat();
    }
  });

  // Send message
  messageForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const text = messageInput.value.trim();
    if (!text || !activePeerId || !ws || ws.readyState !== WebSocket.OPEN) return;

    ws.send(JSON.stringify({
      type: 'send_message',
      recipientId: activePeerId,
      text
    }));

    messageInput.value = '';
    messageInput.focus();
  });
}

// Start chat logic
async function handleStartChat() {
  showInputError('');
  const peerId = peerInput.value.trim();

  if (!/^\d{8}$/.test(peerId)) {
    showInputError('Please enter a valid 8-digit number.');
    return;
  }

  if (peerId === myUserId) {
    showInputError('Cannot start chat with your own 8-digit ID.');
    return;
  }

  peerInput.value = '';
  await selectPeerChat(peerId);
}

function showInputError(msg) {
  inputError.textContent = msg || '';
}

// Select active conversation
async function selectPeerChat(peerId) {
  activePeerId = peerId;
  const conv = getOrCreateConversation(peerId);

  // Fetch status & history from API
  try {
    const statusRes = await fetch(`/api/user-status/${peerId}`);
    if (statusRes.ok) {
      const statusData = await statusRes.json();
      conv.isOnline = statusData.isOnline;
    }

    const historyRes = await fetch(`/api/history?userId=${myUserId}&peerId=${peerId}`);
    if (historyRes.ok) {
      const historyData = await historyRes.json();
      if (historyData.history) {
        conv.messages = historyData.history;
      }
    }
  } catch (err) {
    console.error('Failed to fetch chat history:', err);
  }

  // Update UI
  noChatSelected.classList.add('hidden');
  activeChatView.classList.remove('hidden');

  activePeerIdEl.textContent = peerId;
  updatePeerStatusBadge(conv.isOnline);

  renderMessages(conv.messages);
  renderContactsList();
  messageInput.focus();
}

function updatePeerStatusBadge(isOnline) {
  if (isOnline) {
    peerStatusBadge.textContent = 'Online';
    peerStatusBadge.className = 'status-badge online';
  } else {
    peerStatusBadge.textContent = 'Offline';
    peerStatusBadge.className = 'status-badge offline';
  }
}

// Render contacts sidebar
function renderContactsList() {
  contactsList.innerHTML = '';

  if (conversations.size === 0) {
    contactsList.innerHTML = `<li class="empty-state">No conversations yet. Enter an 8-digit code above to start texting!</li>`;
    return;
  }

  conversations.forEach((conv, peerId) => {
    const li = document.createElement('li');
    li.className = `contact-item ${activePeerId === peerId ? 'active' : ''}`;

    const lastMsg = conv.messages[conv.messages.length - 1];
    const previewText = lastMsg ? lastMsg.text : 'Tap to open chat';

    li.innerHTML = `
      <div class="contact-info">
        <span class="contact-status ${conv.isOnline ? 'online' : ''}"></span>
        <div>
          <div class="contact-id">${peerId}</div>
          <div style="font-size: 0.75rem; color: #94a3b8; max-width: 180px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
            ${escapeHtml(previewText)}
          </div>
        </div>
      </div>
    `;

    li.addEventListener('click', () => {
      selectPeerChat(peerId);
    });

    contactsList.appendChild(li);
  });
}

// Render messages
function renderMessages(messages) {
  messagesContainer.innerHTML = '';
  messages.forEach(msg => {
    appendMessage(msg, msg.senderId === myUserId);
  });
  scrollToBottom();
}

function appendMessage(msg, isSent) {
  const div = document.createElement('div');
  div.className = `msg-bubble ${isSent ? 'sent' : 'received'}`;

  const timeStr = new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  div.innerHTML = `
    <div class="msg-text">${escapeHtml(msg.text)}</div>
    <div class="msg-time">${timeStr}</div>
  `;

  messagesContainer.appendChild(div);
  scrollToBottom();
}

function scrollToBottom() {
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
