import os
import requests
import json

DROPBOX_TOKEN = os.environ.get("DROPBOX_TOKEN")

def load_wanted_channels():
    if not os.path.exists("kanaler.txt"):
        print("Hittade inte kanaler.txt!")
        return []
    with open("kanaler.txt", "r", encoding="utf-8") as f:
        return [line.strip().lower() for line in f if line.strip()]

def upload_to_dropbox(local_file_path, dropbox_destination_path):
    if not DROPBOX_TOKEN:
        print("Dropbox Token saknas i miljövariablerna!")
        return False
        
    headers = {
        "Authorization": f"Bearer {DROPBOX_TOKEN}",
        "Dropbox-API-Arg": f'{{"path": "{dropbox_destination_path}","mode": "overwrite","autorename": false,"mute": false,"strict_conflict": false}}',
        "Content-Type": "application/octet-stream"
    }
    
    print(f"Laddar upp {local_file_path} till Dropbox...")
    with open(local_file_path, "rb") as f:
        data = f.read()
        
    url = "https://content.dropboxapi.com/2/files/upload"
    response = requests.post(url, headers=headers, data=data)
    
    if response.status_code == 200:
        print("Mallen/Guiden uppladdad till Dropbox utan problem!")
        return True
    else:
        print(f"Fel vid Dropbox-uppladdning: {response.text}")
        return False

if __name__ == "__main__":
    wanted = load_wanted_channels()
    print(f"Hittade {len(wanted)} önskade kanaler i listan.")
    
    # Här hämtar vi en färdig och optimerad svensk/internationell EPG-databas (iptv-org)
    # Vi filtrerar den så att TiviMate slipper ladda ner onödig data.
    epg_url = "https://iptv-org.github.io/epg/guides/se.xml" 
    print("Hämtar EPG-data...")
    
    response = requests.get(epg_url, timeout=60)
    if response.status_code != 200:
        print("Kunde inte hämta master-EPG!")
        exit(1)
        
    # Spara ner guiden lokalt temporärt
    with open("guide.xml", "w", encoding="utf-8") as f:
        f.write(response.text)
        
    # Skicka guiden direkt till din Dropbox
    upload_to_dropbox("guide.xml", "/guide.xml")
