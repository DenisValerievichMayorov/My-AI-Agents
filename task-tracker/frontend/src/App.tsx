import { useState, useEffect } from 'react';

interface Task {
  id: number;
  text: string;
  completed: boolean;
  reminderTime: string | null;
  leadTimeMinutes: number;
  notified: boolean;
}

function App() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [inputText, setInputText] = useState('');
  const [reminderTime, setReminderTime] = useState('');
  const [leadTime, setLeadTime] = useState('0');
  const [isAdding, setIsAdding] = useState(false);

  useEffect(() => {
    fetchTasks();
    const interval = setInterval(fetchTasks, 4000);
    
    if ("Notification" in window && Notification.permission === "default") {
      Notification.requestPermission();
    }

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    tasks.forEach(task => {
      if (task.notified && !task.completed) {
        showNotification(task);
      }
    });
  }, [tasks]);

  const showNotification = (task: Task) => {
    const notifiedKey = `notified_${task.id}`;
    if (!sessionStorage.getItem(notifiedKey)) {
      const msg = task.leadTimeMinutes > 0 
        ? `Начнется через ${task.leadTimeMinutes} мин: ${task.text}`
        : `Начинается: ${task.text}`;

      if (Notification.permission === "granted") {
        new Notification("Напоминание!", { body: msg });
        sessionStorage.setItem(notifiedKey, "true");
      } else {
        alert(msg);
        sessionStorage.setItem(notifiedKey, "true");
      }
    }
  };

  const fetchTasks = async () => {
    try {
      const response = await fetch('/api/tasks');
      if (response.ok) {
        const data = await response.json();
        setTasks(data);
      }
    } catch (error) {
      console.error('Connection error:', error);
    }
  };

  const addTask = async () => {
    if (!inputText.trim() || isAdding) return;
    
    setIsAdding(true);
    try {
      const response = await fetch('/api/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          text: inputText,
          reminderTime: reminderTime || null,
          leadTimeMinutes: parseInt(leadTime)
        }),
      });
      
      if (response.ok) {
        const newTask = await response.json();
        setTasks(prev => [...prev, newTask]);
        setInputText('');
        setReminderTime('');
        setLeadTime('0');
      } else {
        alert("Ошибка сервера при добавлении задачи");
      }
    } catch (error) {
      alert("Не удалось связаться с сервером. Проверьте запуск бэкенда.");
    } finally {
      setIsAdding(false);
    }
  };

  const toggleTask = async (id: number) => {
    try {
      const response = await fetch(`/api/tasks/${id}`, { method: 'PATCH' });
      if (response.ok) {
        const updatedTask = await response.json();
        setTasks(tasks.map(t => (t.id === id ? updatedTask : t)));
      }
    } catch (error) {
      console.error('Error toggling task:', error);
    }
  };

  const deleteTask = async (id: number) => {
    try {
      const response = await fetch(`/api/tasks/${id}`, { method: 'DELETE' });
      if (response.ok) {
        setTasks(tasks.filter(t => t.id !== id));
      }
    } catch (error) {
      console.error('Error deleting task:', error);
    }
  };

  const formatTime = (timeStr: string) => {
    const date = new Date(timeStr);
    return date.toLocaleString([], { 
      day: 'numeric', 
      month: 'short', 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div className="app-wrapper">
      <header>
        <h1>Smart Tasks</h1>
        <p className="subtitle">Планируй красиво и вовремя</p>
      </header>

      <main>
        <div className="add-card">
          <input 
            type="text" 
            placeholder="Что нужно сделать?" 
            value={inputText}
            className="input-field"
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && addTask()}
            disabled={isAdding}
          />
          <div className="controls-row">
            <input 
              type="datetime-local" 
              value={reminderTime}
              className="datetime-picker"
              onChange={(e) => setReminderTime(e.target.value)}
              disabled={isAdding}
            />
            <select 
              value={leadTime} 
              className="lead-select"
              onChange={(e) => setLeadTime(e.target.value)}
              disabled={isAdding}
            >
              <option value="0">В срок</option>
              <option value="5">За 5 мин</option>
              <option value="15">За 15 мин</option>
              <option value="30">За 30 мин</option>
              <option value="60">За 1 час</option>
            </select>
          </div>
          <button 
            className="add-button" 
            onClick={addTask}
            disabled={isAdding || !inputText.trim()}
          >
            {isAdding ? "Добавление..." : "Добавить задачу"}
          </button>
        </div>

        <div className="tasks-container">
          {tasks.length === 0 ? (
            <div className="empty-state">Список пока пуст. Самое время что-то запланировать!</div>
          ) : (
            tasks.map(task => (
              <div 
                key={task.id} 
                className={`task-card ${task.completed ? 'completed' : ''} ${task.notified ? 'due' : ''}`}
              >
                <div className="custom-checkbox" onClick={() => toggleTask(task.id)}></div>
                <div className="task-info" onClick={() => toggleTask(task.id)}>
                  <span className="task-title">{task.text}</span>
                  {task.reminderTime && (
                    <span className={`task-meta ${task.notified ? 'warning' : ''}`}>
                      {task.notified ? "⚠️ Время пришло!" : `🔔 ${formatTime(task.reminderTime)}`}
                      {task.leadTimeMinutes > 0 && !task.notified && ` (-${task.leadTimeMinutes}м)`}
                    </span>
                  )}
                </div>
                <button className="delete-icon" onClick={() => deleteTask(task.id)}>
                  &times;
                </button>
              </div>
            ))
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
