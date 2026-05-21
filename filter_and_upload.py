import os
import requests
import xml.etree.ElementTree as ET
import sys

# Hämta miljövariabler för Refresh Token-flödet
REFRESH_TOKEN = os.environ.get("DROPBOX_REFRESH_TOKEN")
APP_KEY = os.environ.get("DROPBOX_APP_KEY")
APP_SECRET = os.environ.get("DROPBOX_APP_SECRET")

def get_access_token():
    """Hämtar en ny giltig access_token från Dropbox."""
    if not all([REFRESH_TOKEN, APP_KEY, APP_SECRET]):
        print("Fel: Saknar nödvändiga Dropbox-miljövariabler!")
        sys.exit(1)
        
    url = "https://api.dropbox.com/oauth2/token"
    params = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
        "client_id": APP_KEY,
        "client_secret": APP_SECRET
    }
    response = requests.post(url, data=params)
    
    if response.status_code != 200:
        print(f"Fel vid hämtning av access_token: {response.text}")
        sys.exit(1)
        
    return response.json()["access_token"]

def upload_to_dropbox(local_file_path, dropbox_destination_path):
    access_token = get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Dropbox-API-Arg": f'{{"path": "{dropbox_destination_path}","mode": "overwrite"}}',
        "Content-Type": "application/octet-stream"
    }
    
    print(f"Laddar upp {local_file_path} till Dropbox...")
    with open(local_file_path, "rb") as f:
        data = f.read()
    
    url = "https://content.dropboxapi.com/2/files/upload"
    response = requests.post(url, headers=headers, data=data)
    
    if response.status_code == 200:
        print("Guiden har laddats upp till din Dropbox!")
        return True
    else:
        print(f"Fel vid Dropbox-uppladdning: {response.text}")
        return False

if __name__ == "__main__":
    # Eftersom du nu kör filtreringen redan i 'grab'-steget med my_channels.xml,
    # så behöver vi bara ladda upp filen 'guide.xml' direkt.
    raw_file = "guide.xml" 
    
    if not os.path.exists(raw_file):
        print(f"Hittade inte {raw_file}! Avbryter.")
        sys.exit(1)
    
    # Ladda upp filen direkt till Dropbox
    if upload_to_dropbox(raw_file, "/guide.xml"):
        sys.exit(0)
    else:
        sys.exit(1)
