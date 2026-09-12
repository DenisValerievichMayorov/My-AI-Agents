let myUserId = null;
let activePeerId = null;

// PeerJS & WebSocket instances
let peer = null;
let ws = null;
// Active PeerJS DataConnections: Map<peerId, DataConnection>
const peerConnections = new Map();

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
  setupUserIdentity();
  initPeerJS();
  connectWebSocketFallback();
  setupEventListeners();
}

// 1. Get or Generate 8-digit User ID
function setupUserIdentity() {
  let storedId = localStorage.getItem('messenger_8digit_id');
  if (!storedId || !/^\d{8}$/.test(storedId)) {
    storedId = Math.floor(10000000 + Math.random() * 90000000).toString();
    localStorage.setItem('messenger_8digit_id', storedId);
  }

  myUserId = storedId;
  myUserIdEl.textContent = myUserId;
}

// Prefix peer IDs to avoid collisions on public cloud PeerJS broker while keeping UI 8-digit
const PEER_PREFIX = 'msg8d_';

// 2. Initialize PeerJS P2P (Serverless for GitHub Pages)
function initPeerJS() {
  if (typeof Peer === 'undefined') {
    console.warn('PeerJS library not available, using WebSocket fallback.');
    return;
  }

  try {
    peer = new Peer(PEER_PREFIX + myUserId, {
      debug: 1
    });

    peer.on('open', (id) => {
      console.log('PeerJS connected with 8-digit peer ID:', myUserId);
    });

    // Handle incoming P2P connections
    peer.on('connection', (conn) => {
      setupDataConnection(conn);
    });

    peer.on('error', (err) => {
      console.warn('PeerJS error:', err.type, err);
      if (err.type === 'peer-unavailable') {
        showInputError('User ' + activePeerId + ' is offline or ID does not exist.');
      }
    });
  } catch (err) {
    console.warn('PeerJS init failed:', err);
  }
}

// Setup incoming/outgoing DataConnection
function setupDataConnection(conn) {
  const rawPeerId = conn.peer.replace(PEER_PREFIX, '');

  conn.on('open', () => {
    peerConnections.set(rawPeerId, conn);
    const conv = getOrCreateConversation(rawPeerId);
    conv.isOnline = true;

    if (activePeerId === rawPeerId) {
      updatePeerStatusBadge(true);
    }
    renderContactsList();
  });

  conn.on('data', (data) => {
    if (data && data.type === 'chat_message') {
      const { message } = data;
      const conv = getOrCreateConversation(rawPeerId);
      conv.messages.push(message);

      if (activePeerId === rawPeerId) {
        appendMessage(message, false);
      }
      renderContactsList();
    }
  });

  conn.on('close', () => {
    peerConnections.delete(rawPeerId);
    const conv = getOrCreateConversation(rawPeerId);
    conv.isOnline = false;

    if (activePeerId === rawPeerId) {
      updatePeerStatusBadge(false);
    }
    renderContactsList();
  });
}

// Connect to a peer via PeerJS
function connectToPeerJS(target8DigitId) {
  if (!peer || peer.destroyed) return null;

  const existingConn = peerConnections.get(target8DigitId);
  if (existingConn && existingConn.open) {
    return existingConn;
  }

  const conn = peer.connect(PEER_PREFIX + target8DigitId);
  setupDataConnection(conn);
  return conn;
}

// 3. Connect WebSocket (Fallback for local server)
function connectWebSocketFallback() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}`;

  try {
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      ws.send(JSON.stringify({
        type: 'register',
        userId: myUserId
      }));
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleWsMessage(data);
      } catch (err) {
        console.error('WS parse error:', err);
      }
    };

    ws.onclose = () => {};
    ws.onerror = () => {};
  } catch (e) {
    // Ignore WS failure on pure static GitHub Pages hosting
  }
}

function handleWsMessage(data) {
  switch (data.type) {
    case 'registered':
      if (data.onlineUsers && Array.isArray(data.onlineUsers)) {
        data.onlineUsers.forEach(peerId => {
          getOrCreateConversation(peerId).isOnline = true;
        });
        renderContactsList();
      }
      break;

    case 'user_status': {
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
    }

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
  copyIdBtn.addEventListener('click', () => {
    navigator.clipboard.writeText(myUserId);
    const origText = copyIdBtn.textContent;
    copyIdBtn.textContent = '✓';
    setTimeout(() => copyIdBtn.textContent = origText, 1500);
  });

  regenIdBtn.addEventListener('click', () => {
    localStorage.removeItem('messenger_8digit_id');
    location.reload();
  });

  startChatBtn.addEventListener('click', () => {
    handleStartChat();
  });

  peerInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      handleStartChat();
    }
  });

  messageForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const text = messageInput.value.trim();
    if (!text || !activePeerId) return;

    const msgObj = {
      id: 'msg_' + Date.now() + '_' + Math.random().toString(36).substr(2, 5),
      senderId: myUserId,
      recipientId: activePeerId,
      text: text,
      timestamp: new Date().toISOString()
    };

    let sentViaP2P = false;
    const p2pConn = peerConnections.get(activePeerId);

    if (p2pConn && p2pConn.open) {
      p2pConn.send({ type: 'chat_message', message: msgObj });
      sentViaP2P = true;
    }

    let sentViaWS = false;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'send_message',
        recipientId: activePeerId,
        text
      }));
      sentViaWS = true;
    }

    if (sentViaP2P && !sentViaWS) {
      // Local append if sent directly via P2P
      const conv = getOrCreateConversation(activePeerId);
      conv.messages.push(msgObj);
      appendMessage(msgObj, true);
      renderContactsList();
    } else if (!sentViaP2P && !sentViaWS) {
      // Attempt connecting on demand
      const conn = connectToPeerJS(activePeerId);
      if (conn) {
        conn.on('open', () => {
          conn.send({ type: 'chat_message', message: msgObj });
          const conv = getOrCreateConversation(activePeerId);
          conv.messages.push(msgObj);
          appendMessage(msgObj, true);
          renderContactsList();
        });
      }
    }

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

  // Connect via PeerJS WebRTC
  connectToPeerJS(peerId);

  // Also query REST API if available
  try {
    const statusRes = await fetch(`/api/user-status/${peerId}`);
    if (statusRes.ok) {
      const statusData = await statusRes.json();
      if (statusData.isOnline) conv.isOnline = true;
    }

    const historyRes = await fetch(`/api/history?userId=${myUserId}&peerId=${peerId}`);
    if (historyRes.ok) {
      const historyData = await historyRes.json();
      if (historyData.history && historyData.history.length > 0) {
        conv.messages = historyData.history;
      }
    }
  } catch (err) {
    // Static hosting mode without REST backend
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
