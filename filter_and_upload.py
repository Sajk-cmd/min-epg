import os
import requests
import xml.etree.ElementTree as ET

DROPBOX_TOKEN = os.environ.get("DROPBOX_TOKEN")

def load_wanted_channels():
    if not os.path.exists("kanaler.txt"):
        print("Hittade inte kanaler.txt! Laddar upp hela guiden ofiltrerad...")
        return None
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
    raw_file = "guide_raw.xml"
    output_file = "guide.xml"
    
    if not os.path.exists(raw_file):
        print("Hittade ingen genererad guide_raw.xml från tv.nu!")
        exit(1)
        
    if wanted_channels is None:
        upload_to_dropbox(raw_file, "/guide.xml")
        exit(0)
        
    print(f"Filtrerar guiden för {len(wanted_channels)} önskade kanaler...")
    
    try:
        tree = ET.parse(raw_file)
        root = tree.getroot()
        
        new_root = ET.Element("tv")
        if "generator-info-name" in root.attrib:
            new_root.set("generator-info-name", root.attrib["generator-info-name"])
            
        # Skapa en ordbok (dictionary) för att mappa både tv.nu-id och display-name
        allowed_channel_ids = set()
        channel_map = {} # Mappar det interna ID:t till det snygga namnet
        
        # 1. Hitta alla godkända kanaler
        for channel in root.findall("channel"):
            channel_id = channel.get("id")
            display_name = channel.find("display-name")
            
            if display_name is not None and display_name.text:
                clean_name = display_name.text.lower().replace(" ", "")
                if clean_name in wanted_channels:
                    new_root.append(channel)
                    allowed_channel_ids.add(channel_id)
                    # Spara även en rensad version av ID-strängen ifall programmen använder ett kortare ID
                    short_id = channel_id.split("@")[0].lower() if "@" in channel_id else channel_id.lower()
                    channel_map[short_id] = channel_id

        # 2. Gå igenom alla program och matcha mot våra tillåtna kanaler
        program_count = 0
        for programme in root.findall("programme"):
            prog_channel = programme.get("channel")
            if not prog_channel:
                continue
                
            prog_channel_clean = prog_channel.lower()
            
            # Kolla om programmets kanal-ID matchar direkt eller via vårt kortare ID
            if prog_channel in allowed_channel_ids:
                new_root.append(programme)
                program_count += 1
            elif prog_channel_clean in channel_map:
                # Om programmet använder det korta ID:t (t.ex. 'svt1.se'), tvinga det att använda det fulla ID:t
                programme.set("channel", channel_map[prog_channel_clean])
                new_root.append(programme)
                program_count += 1
            elif prog_channel_clean.split(".")[0] in channel_map:
                # Fallback för rent tv.nu-id (t.ex. 'svt1')
                pure_id = prog_channel_clean.split(".")[0]
                programme.set("channel", channel_map[pure_id])
                new_root.append(programme)
                program_count += 1
                
        print(f"Filtrering klar: Sparade {len(allowed_channel_ids)} kanaler med totalt {program_count} program.")
        
        new_tree = ET.ElementTree(new_root)
        new_tree.write(output_file, encoding="utf-8", xml_declaration=True)
        
        # Ladda upp till Dropbox
        upload_to_dropbox(output_file, "/guide.xml")
        
    except Exception as e:
        print(f"Ett fel uppstod vid filtrering av XML: {e}")
        exit(1)
