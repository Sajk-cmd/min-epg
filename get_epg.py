import os
import requests
import xml.etree.ElementTree as ET

DROPBOX_TOKEN = os.environ.get("DROPBOX_TOKEN")

def load_wanted_channels():
    if not os.path.exists("kanaler.txt"):
        print("Hittade inte kanaler.txt!")
        return []
    with open("kanaler.txt", "r", encoding="utf-8") as f:
        # Sparar namnen i lowercase och rensar mellanslag för säkrare matchning
        return [line.strip().lower().replace(" ", "") for line in f if line.strip()]

def upload_to_dropbox(local_file_path, dropbox_destination_path):
    if not DROPBOX_TOKEN:
        print("Dropbox Token saknas helt i GitHub Secrets! Kontrollera inställningarna.")
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
        print("Guiden har laddats upp till din Dropbox!")
        return True
    else:
        print(f"Fel vid Dropbox-uppladdning: {response.text}")
        return False

if __name__ == "__main__":
    wanted_channels = load_wanted_channels()
    print(f"Hittade {len(wanted_channels)} önskade kanaler i kanaler.txt.")
    
    # Vi använder en mycket stabil och öppen XMLTV-källa för Skandinavien
    epg_url = "https://raw.githubusercontent.com/HelmerLator/Sweden-EPG/main/Sweden.xml"
    print("Hämtar EPG-data...")
    
    response = requests.get(epg_url, timeout=60)
    if response.status_code != 200:
        print(f"Kunde inte hämta EPG-data (Statuskod: {response.status_code})")
        exit(1)
        
    print("EPG nedladdad. Filtrerar ut dina valda kanaler...")
    
    try:
        # Läs in XML-datan
        root = ET.fromstring(response.content)
        
        # Skapa ett nytt tomt XML-träd för din anpassade guide
        new_root = ET.Element("tv")
        if "generator-info-name" in root.attrib:
            new_root.set("generator-info-name", root.attrib["generator-info-name"])
            
        # Hitta de kanal-IDn som matchar namnen i din textfil
        matched_channel_ids = set()
        
        for channel in root.findall("channel"):
            display_name = channel.find("display-name")
            if display_name is not None and display_name.text:
                clean_name = display_name.text.lower().replace(" ", "")
                # Om kanalnamnet finns i din lista, spara den och dess ID
                if clean_name in wanted_channels:
                    new_root.append(channel)
                    matched_channel_ids.add(channel.get("id"))
        
        # Gå igenom alla program och behåll bara de som hör till dina matchade kanaler
        program_count = 0
        for programme in root.findall("programme"):
            channel_id = programme.get("channel")
            if channel_id in matched_channel_ids:
                new_root.append(programme)
                program_count += 1
                
        print(f"Matchade {len(matched_channel_ids)} kanaler med totalt {program_count} program.")
        
        # Spara den nya slimmade guiden lokalt
        tree = ET.ElementTree(new_root)
        tree.write("guide.xml", encoding="utf-8", xml_declaration=True)
        
        # Ladda upp till Dropbox
        upload_to_dropbox("guide.xml", "/guide.xml")
        
    except Exception as e:
        print(f"Ett fel uppstod vid filtrering av XML: {e}")
        exit(1)
