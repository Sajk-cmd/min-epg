import os
import requests
import xml.etree.ElementTree as ET

DROPBOX_TOKEN = os.environ.get("DROPBOX_TOKEN")

def load_wanted_channels():
    if not os.path.exists("kanaler.txt"):
        print("Hittade inte kanaler.txt!")
        return []
    with open("kanaler.txt", "r", encoding="utf-8") as f:
        return [line.strip().lower().replace(" ", "") for line in f if line.strip()]

def upload_to_dropbox(local_file_path, dropbox_destination_path):
    if not DROPBOX_TOKEN:
        print("Dropbox Token saknas i GitHub Secrets!")
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
    output_file = "guide.xml"
    
    print(f"Hittade {len(wanted_channels)} önskade kanaler i kanaler.txt.")
    
    # Den RÄTTA, existerande URL:en (Ren XML, ej komprimerad)
    epg_url = "https://iptv-org.github.io/epg/guides/se/tv.nu.xml"
    print("Hämtar färdig EPG-data från iptv-org...")
    
    response = requests.get(epg_url, timeout=60)
    if response.status_code != 200:
        print(f"Kunde inte hämta EPG (Status: {response.status_code})")
        exit(1)
        
    print("EPG nedladdad utan problem. Filtrerar...")
    
    try:
        # Läs XML direkt från texten eftersom den inte är komprimerad
        root = ET.fromstring(response.content)
        
        new_root = ET.Element("tv")
        if "generator-info-name" in root.attrib:
            new_root.set("generator-info-name", root.attrib["generator-info-name"])
            
        allowed_channel_ids = set()
        channel_map = {}
        
        # 1. Hitta kanalerna
        for channel in root.findall("channel"):
            channel_id = channel.get("id")
            display_name = channel.find("display-name")
            
            if display_name is not None and display_name.text:
                clean_name = display_name.text.lower().replace(" ", "")
                if clean_name in wanted_channels:
                    new_root.append(channel)
                    allowed_channel_ids.add(channel_id)
                    
                    short_id = channel_id.split("@")[0].lower() if "@" in channel_id else channel_id.lower()
                    channel_map[short_id] = channel_id

        # 2. Matchar programmen
        program_count = 0
        for programme in root.findall("programme"):
            prog_channel = programme.get("channel")
            if not prog_channel:
                continue
                
            prog_channel_clean = prog_channel.lower()
            
            if prog_channel in allowed_channel_ids:
                new_root.append(programme)
                program_count += 1
            elif prog_channel_clean in channel_map:
                programme.set("channel", channel_map[prog_channel_clean])
                new_root.append(programme)
                program_count += 1
                
        print(f"Filtrering klar: Sparade {len(allowed_channel_ids)} kanaler med totalt {program_count} program.")
        
        new_tree = ET.ElementTree(new_root)
        new_tree.write(output_file, encoding="utf-8", xml_declaration=True)
        
        upload_to_dropbox(output_file, "/guide.xml")
        
    except Exception as e:
        print(f"Ett fel uppstod vid hantering av XML: {e}")
        exit(1)
