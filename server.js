const express = require('express');
const http = require('http');
const path = require('path');
const WebSocket = require('ws');

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Store active WebSocket connections by 8-digit user ID
// Map<userId, Set<WebSocket>>
const clients = new Map();

// In-memory message store: array of { id, senderId, recipientId, text, timestamp }
const messageStore = [];

/**
 * Generates a random 8-digit numeric string (10000000 - 99999999)
 */
function generate8DigitId() {
  return Math.floor(10000000 + Math.random() * 90000000).toString();
}

/**
 * Helper to broadcast online status update or peer updates
 */
function notifyUserStatusChange(userId, isOnline) {
  const statusPayload = JSON.stringify({
    type: 'user_status',
    userId,
    isOnline
  });

  clients.forEach((sockets, clientUserId) => {
    if (clientUserId !== userId) {
      sockets.forEach(ws => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(statusPayload);
        }
      });
    }
  });
}

/**
 * Send helper
 */
function sendToUser(userId, payload) {
  const userSockets = clients.get(userId);
  if (userSockets && userSockets.size > 0) {
    const data = typeof payload === 'string' ? payload : JSON.stringify(payload);
    userSockets.forEach(ws => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(data);
      }
    });
    return true;
  }
  return false;
}

// WebSocket connection handler
wss.on('connection', (ws) => {
  let currentUserId = null;

  ws.on('message', (messageRaw) => {
    try {
      const data = JSON.parse(messageRaw);

      switch (data.type) {
        case 'register': {
          const { userId } = data;
          if (!userId || !/^\d{8}$/.test(userId)) {
            ws.send(JSON.stringify({ type: 'error', message: 'Invalid 8-digit user ID.' }));
            return;
          }

          currentUserId = userId;
          if (!clients.has(currentUserId)) {
            clients.set(currentUserId, new Set());
          }
          clients.get(currentUserId).add(ws);

          ws.send(JSON.stringify({
            type: 'registered',
            userId: currentUserId,
            onlineUsers: Array.from(clients.keys()).filter(id => id !== currentUserId)
          }));

          notifyUserStatusChange(currentUserId, true);
          break;
        }

        case 'send_message': {
          if (!currentUserId) {
            ws.send(JSON.stringify({ type: 'error', message: 'Not registered yet.' }));
            return;
          }

          const { recipientId, text } = data;

          if (!recipientId || !/^\d{8}$/.test(recipientId)) {
            ws.send(JSON.stringify({ type: 'error', message: 'Recipient ID must be an 8-digit number.' }));
            return;
          }

          if (recipientId === currentUserId) {
            ws.send(JSON.stringify({ type: 'error', message: 'Cannot text yourself.' }));
            return;
          }

          if (!text || typeof text !== 'string' || text.trim().length === 0) {
            ws.send(JSON.stringify({ type: 'error', message: 'Message text cannot be empty.' }));
            return;
          }

          const msgObj = {
            id: 'msg_' + Date.now() + '_' + Math.random().toString(36).substr(2, 5),
            senderId: currentUserId,
            recipientId: recipientId,
            text: text.trim(),
            timestamp: new Date().toISOString()
          };

          messageStore.push(msgObj);

          // Deliver to recipient if online
          const delivered = sendToUser(recipientId, {
            type: 'new_message',
            message: msgObj
          });

          // Confirm delivery to sender
          ws.send(JSON.stringify({
            type: 'message_sent',
            message: msgObj,
            delivered
          }));

          break;
        }

        default:
          ws.send(JSON.stringify({ type: 'error', message: 'Unknown action type.' }));
      }
    } catch (err) {
      ws.send(JSON.stringify({ type: 'error', message: 'Invalid message payload.' }));
    }
  });

  ws.on('close', () => {
    if (currentUserId && clients.has(currentUserId)) {
      const userSockets = clients.get(currentUserId);
      userSockets.delete(ws);
      if (userSockets.size === 0) {
        clients.delete(currentUserId);
        notifyUserStatusChange(currentUserId, false);
      }
    }
  });
});

// REST Endpoints

// Generate a new unique 8-digit ID for a client
app.get('/api/generate-id', (req, res) => {
  let newId;
  let attempts = 0;
  do {
    newId = generate8DigitId();
    attempts++;
  } while (clients.has(newId) && attempts < 100);

  res.json({ userId: newId });
});

// Check if an 8-digit user ID is valid format and currently online
app.get('/api/user-status/:userId', (req, res) => {
  const { userId } = req.params;
  const is8Digits = /^\d{8}$/.test(userId);
  if (!is8Digits) {
    return res.status(400).json({ error: 'User ID must be an 8-digit number.' });
  }

  const isOnline = clients.has(userId) && clients.get(userId).size > 0;
  const hasHistory = messageStore.some(m => m.senderId === userId || m.recipientId === userId);

  res.json({
    userId,
    isOnline,
    exists: isOnline || hasHistory
  });
});

// Get message history between two user IDs
app.get('/api/history', (req, res) => {
  const { userId, peerId } = req.query;

  if (!userId || !peerId) {
    return res.status(400).json({ error: 'Both userId and peerId query parameters are required.' });
  }

  const history = messageStore.filter(
    msg =>
      (msg.senderId === userId && msg.recipientId === peerId) ||
      (msg.senderId === peerId && msg.recipientId === userId)
  );

  res.json({ history });
});

module.exports = { app, server, wss, clients, messageStore, generate8DigitId };

if (require.main === module) {
  const PORT = process.env.PORT || 3000;
  const HOST = process.env.HOST || '0.0.0.0';
  server.listen(PORT, HOST, () => {
    console.log(`Server listening on http://${HOST}:${PORT}`);
  });
}
