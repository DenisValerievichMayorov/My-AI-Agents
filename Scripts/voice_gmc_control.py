import os
import time
import queue
import sys
import json
import subprocess
from datetime import datetime
import sounddevice as sd
from google.oauth2.credentials import Credentials
from google.cloud import speech

# Настройки
TOKEN_FILE = r'C:\Users\anton\Sync\speech_token.json'
CLIENT_SECRET_FILE = r'C:\Users\anton\Sync\client_secret.json'
RATE = 16000
CHUNK = int(RATE / 10)

# Маппинг голосовых команд
COMMANDS = {
    "панель": {
        "action": ["py", r"C:\Users\anton\Sync\Scripts\launch_dashboard.py"],
        "msg": "🚀 Запускаю веб-панель GMC..."
    },
    "статус": {
        "action": ["py", r"C:\Users\anton\Sync\Scripts\heartbeat.py"],
        "msg": "📊 Проверяю статус агентов..."
    },
    "синхронизация": {
        "action": ["start", "http://localhost:8384"],
        "msg": "🔄 Открываю страницу синхронизации Syncthing..."
    },
    "отчет": {
        "action": ["py", r"C:\Users\anton\Sync\Scripts\generate_pdf_report.py"],
        "msg": "📝 Запускаю генератор отчетов..."
    }
}

class ResumableMicrophoneStream:
    def __init__(self, rate, chunk_size):
        self._rate = rate
        self._chunk_size = chunk_size
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self.closed = False
        self._stream = sd.RawInputStream(
            samplerate=self._rate, blocksize=self._chunk_size,
            device=None, dtype='int16', channels=1, callback=self._fill_buffer
        )
        self._stream.start()
        return self

    def __exit__(self, type, value, traceback):
        self._stream.stop()
        self._stream.close()
        self.closed = True
        self._buff.put(None)

    def _fill_buffer(self, indata, frames, time, status):
        self._buff.put(bytes(indata))

    def generator(self):
        while not self.closed:
            chunk = self._buff.get()
            if chunk is None: return
            yield chunk

def get_credentials():
    with open(TOKEN_FILE, 'r') as f:
        token_data = json.load(f)
    with open(CLIENT_SECRET_FILE, 'r') as f:
        client_data = json.load(f)['installed']
    return Credentials(
        token=token_data.get('access_token'),
        refresh_token=token_data.get('refresh_token'),
        token_uri=client_data.get('token_uri'),
        client_id=client_data.get('client_id'),
        client_secret=client_data.get('client_secret'),
        scopes=token_data.get('scope').split() if isinstance(token_data.get('scope'), str) else token_data.get('scope')
    )

def execute_command(text):
    text = text.lower()
    for trigger, data in COMMANDS.items():
        if trigger in text:
            print(f"\n[Голосовая команда] {data['msg']}")
            if data['action'][0] == "start":
                subprocess.Popen(f"start {data['action'][1]}", shell=True)
            else:
                subprocess.Popen(data['action'])
            return True
    return False

def main():
    creds = get_credentials()
    client = speech.SpeechClient(credentials=creds)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code="ru-RU",
    )
    streaming_config = speech.StreamingRecognitionConfig(
        config=config, interim_results=True
    )

    print("--- GMC VOICE CONTROL ACTIVE ---")
    print("Команды: 'панель', 'статус', 'синхронизация', 'отчет'")
    print("--------------------------------")

    with ResumableMicrophoneStream(RATE, CHUNK) as stream:
        while True:
            print("Слушаю команду...")
            audio_generator = stream.generator()
            requests = (speech.StreamingRecognizeRequest(audio_content=content) for content in audio_generator)
            responses = client.streaming_recognize(streaming_config, requests)

            for response in responses:
                if not response.results: continue
                result = response.results[0]
                if not result.alternatives: continue
                
                transcript = result.alternatives[0].transcript
                print(f"Распознано: {transcript}", end="\r")

                if result.is_final:
                    if execute_command(transcript):
                        print("\nКоманда выполнена. Жду следующую...")
                        break # Начинаем новый цикл прослушивания после выполнения команды
                    else:
                        print(f"\nНеизвестная команда: {transcript}")
                        break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nГолосовое управление остановлено.")
    except Exception as e:
        print(f"\nОшибка: {e}")
