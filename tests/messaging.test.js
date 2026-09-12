const assert = require('assert');
const http = require('http');
const WebSocket = require('ws');
const { app, server, generate8DigitId, clients, messageStore } = require('../server');

async function runTests() {
  console.log('Running 8-Digit Messaging Application tests...');
  let testServer;
  let serverPort;

  await new Promise((resolve) => {
    testServer = server.listen(0, () => {
      serverPort = testServer.address().port;
      resolve();
    });
  });

  try {
    // Test 1: ID generation
    console.log('Test 1: ID generation format');
    for (let i = 0; i < 50; i++) {
      const id = generate8DigitId();
      assert.strictEqual(typeof id, 'string');
      assert.strictEqual(id.length, 8);
      assert.ok(/^\d{8}$/.test(id), `Expected 8 digits, got ${id}`);
    }

    // Test 2: GET /api/generate-id
    console.log('Test 2: GET /api/generate-id endpoint');
    const generatedRes = await new Promise((resolve, reject) => {
      http.get(`http://localhost:${serverPort}/api/generate-id`, (res) => {
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => resolve(JSON.parse(data)));
      }).on('error', reject);
    });
    assert.ok(generatedRes.userId);
    assert.ok(/^\d{8}$/.test(generatedRes.userId));

    // Test 3: GET /api/user-status/:userId
    console.log('Test 3: GET /api/user-status/:userId endpoint');
    const statusStatusCode = await new Promise((resolve) => {
      http.get(`http://localhost:${serverPort}/api/user-status/invalid`, (res) => {
        resolve(res.statusCode);
      });
    });
    assert.strictEqual(statusStatusCode, 400);

    const validStatus = await new Promise((resolve) => {
      http.get(`http://localhost:${serverPort}/api/user-status/12345678`, (res) => {
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => resolve(JSON.parse(data)));
      });
    });
    assert.strictEqual(validStatus.userId, '12345678');
    assert.strictEqual(validStatus.isOnline, false);

    // Test 4: Realtime messaging between 2 users
    console.log('Test 4: WebSocket real-time message exchange by 8-digit ID');
    await new Promise((resolve, reject) => {
      const userA = '11112222';
      const userB = '33334444';

      const wsA = new WebSocket(`ws://localhost:${serverPort}`);
      const wsB = new WebSocket(`ws://localhost:${serverPort}`);

      let userARegistered = false;
      let userBRegistered = false;

      function checkReady() {
        if (userARegistered && userBRegistered) {
          wsA.send(JSON.stringify({
            type: 'send_message',
            recipientId: userB,
            text: 'Hello from User A!'
          }));
        }
      }

      wsA.on('open', () => {
        wsA.send(JSON.stringify({ type: 'register', userId: userA }));
      });

      wsB.on('open', () => {
        wsB.send(JSON.stringify({ type: 'register', userId: userB }));
      });

      wsA.on('message', (raw) => {
        const msg = JSON.parse(raw);
        if (msg.type === 'registered') {
          userARegistered = true;
          checkReady();
        } else if (msg.type === 'message_sent') {
          assert.strictEqual(msg.message.senderId, userA);
          assert.strictEqual(msg.message.recipientId, userB);
          assert.strictEqual(msg.delivered, true);
        }
      });

      wsB.on('message', (raw) => {
        const msg = JSON.parse(raw);
        if (msg.type === 'registered') {
          userBRegistered = true;
          checkReady();
        } else if (msg.type === 'new_message') {
          assert.strictEqual(msg.message.senderId, userA);
          assert.strictEqual(msg.message.text, 'Hello from User A!');
          wsA.close();
          wsB.close();
          resolve();
        }
      });

      wsA.on('error', reject);
      wsB.on('error', reject);
    });

    console.log('All tests passed successfully!');
  } finally {
    await new Promise(res => testServer.close(res));
  }
}

runTests().catch(err => {
  console.error('Test failed:', err);
  process.exit(1);
});
