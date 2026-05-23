import os
import time
import queue
import sys
import json
from datetime import datetime
import sounddevice as sd
from google.oauth2.credentials import Credentials
from google.cloud import speech

# Настройки
TOKEN_FILE = r'C:\Users\anton\Sync\speech_token.json'
CLIENT_SECRET_FILE = r'C:\Users\anton\Sync\client_secret.json'
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms

class ResumableMicrophoneStream:
    def __init__(self, rate, chunk_size):
        self._rate = rate
        self._chunk_size = chunk_size
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self.closed = False
        self._stream = sd.RawInputStream(
            samplerate=self._rate,
            blocksize=self._chunk_size,
            device=None,  # Default device
            dtype='int16',
            channels=1,
            callback=self._fill_buffer
        )
        self._stream.start()
        return self

    def __exit__(self, type, value, traceback):
        self._stream.stop()
        self._stream.close()
        self.closed = True
        self._buff.put(None)

    def _fill_buffer(self, indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        self._buff.put(bytes(indata))

    def generator(self):
        while not self.closed:
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break
            yield b"".join(data)

def get_credentials():
    with open(TOKEN_FILE, 'r') as f:
        token_data = json.load(f)
    with open(CLIENT_SECRET_FILE, 'r') as f:
        client_data = json.load(f)['installed']

    expiry = None
    if 'expiry_date' in token_data:
        expiry = datetime.fromtimestamp(token_data['expiry_date'] / 1000.0)

    return Credentials(
        token=token_data.get('access_token'),
        refresh_token=token_data.get('refresh_token'),
        token_uri=client_data.get('token_uri'),
        client_id=client_data.get('client_id'),
        client_secret=client_data.get('client_secret'),
        scopes=token_data.get('scope').split() if isinstance(token_data.get('scope'), str) else token_data.get('scope'),
        expiry=expiry
    )

def main():
    if not os.path.exists(TOKEN_FILE):
        print(f"Error: Token file not found at {TOKEN_FILE}")
        return
    if not os.path.exists(CLIENT_SECRET_FILE):
        print(f"Error: Client secret file not found at {CLIENT_SECRET_FILE}")
        return

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

    print("--- Запись пошла (говорите в микрофон, запись на 30 секунд) ---")

    with ResumableMicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        requests = (
            speech.StreamingRecognizeRequest(audio_content=content)
            for content in audio_generator
        )

        responses = client.streaming_recognize(streaming_config, requests)

        start_time = time.time()
        for response in responses:
            if time.time() - start_time > 30:
                print("\n--- Время вышло ---")
                break
            if not response.results:
                continue
            result = response.results[0]
            if not result.alternatives:
                continue
            transcript = result.alternatives[0].transcript
            if result.is_final:
                print(f"\nРезультат: {transcript}")
            else:
                print(f"Слушаю: {transcript}", end="\r")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nОстановлено пользователем.")
    except Exception as e:
        print(f"\nОшибка: {e}")
