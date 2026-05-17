const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3001;
const DB_FILE = path.join(__dirname, 'tasks.json');

app.use(cors());
app.use(bodyParser.json());

console.log('--- SERVER STARTING UP ---');

let tasks = [];

// Load tasks from file
try {
  if (fs.existsSync(DB_FILE)) {
    const data = fs.readFileSync(DB_FILE, 'utf8');
    tasks = JSON.parse(data);
    console.log(`Loaded ${tasks.length} tasks from ${DB_FILE}`);
  } else {
    tasks = [
      { id: 1, text: 'Приложение запущено!', completed: false, reminderTime: null, leadTimeMinutes: 0, notified: false }
    ];
    fs.writeFileSync(DB_FILE, JSON.stringify(tasks, null, 2));
    console.log('Created new tasks.json with initial data');
  }
} catch (err) {
  console.error('Error loading tasks:', err);
  tasks = [];
}

const saveTasks = () => {
  try {
    fs.writeFileSync(DB_FILE, JSON.stringify(tasks, null, 2));
  } catch (err) {
    console.error('Error saving tasks:', err);
  }
};

// Периодическая проверка (каждые 3 сек)
setInterval(() => {
  const now = new Date();
  let changed = false;
  tasks.forEach(task => {
    if (task.reminderTime && !task.notified && !task.completed) {
      const reminderDate = new Date(task.reminderTime);
      const leadTimeMs = (parseInt(task.leadTimeMinutes) || 0) * 60 * 1000;
      if (now >= new Date(reminderDate.getTime() - leadTimeMs)) {
        task.notified = true;
        changed = true;
        console.log(`[ALERT] Task "${task.text}" notification triggered`);
      }
    }
  });
  if (changed) saveTasks();
}, 3000);

app.get('/api/tasks', (req, res) => {
  console.log('GET /api/tasks called');
  res.json(tasks);
});

app.post('/api/tasks', (req, res) => {
  console.log('POST /api/tasks called with:', req.body);
  try {
    const { text, reminderTime, leadTimeMinutes } = req.body;
    if (!text) {
      console.log('Error: Missing text');
      return res.status(400).json({ error: 'Text required' });
    }
    const newTask = {
      id: Date.now(),
      text,
      completed: false,
      reminderTime: reminderTime || null,
      leadTimeMinutes: parseInt(leadTimeMinutes) || 0,
      notified: false
    };
    tasks.push(newTask);
    saveTasks();
    console.log('Task saved:', newTask.id);
    res.status(201).json(newTask);
  } catch (err) {
    console.error('Server side error:', err);
    res.status(500).send(err.message);
  }
});

app.patch('/api/tasks/:id', (req, res) => {
  const id = parseInt(req.params.id);
  const task = tasks.find(t => t.id === id);
  if (task) {
    task.completed = !task.completed;
    saveTasks();
    res.json(task);
  } else {
    res.status(404).send('Not found');
  }
});

app.delete('/api/tasks/:id', (req, res) => {
  const id = parseInt(req.params.id);
  tasks = tasks.filter(t => t.id !== id);
  saveTasks();
  res.status(204).send();
});

// Слушаем на 0.0.0.0 для доступности из Termux/Android
app.listen(PORT, '0.0.0.0', () => {
  console.log(`✅ SUCCESS: API server is running on http://0.0.0.0:${PORT}`);
  console.log(`Try: curl http://localhost:${PORT}/api/tasks`);
});

