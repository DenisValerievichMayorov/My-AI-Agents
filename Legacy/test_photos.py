import requests
import json
import os

SYNC_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_PATH = os.path.join(SYNC_DIR, 'google_token.json')

def test_photos_direct():
    with open(TOKEN_PATH, 'r') as f:
        token_data = json.load(f)
    
    access_token = token_data['token']
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    print("Проверка прямого доступа к Google Photos API...")
    url = "https://photoslibrary.googleapis.com/v1/mediaItems?pageSize=1"
    response = requests.get(url, headers=headers)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")

if __name__ == '__main__':
    test_photos_direct()
