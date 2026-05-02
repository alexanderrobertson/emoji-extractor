import os
import re
import json
import requests
import urllib.request

VERSIONS = ['4.0', '5.0', '11.0', '12.0', '12.1', '13.0', '14.0', '15.0', '15.1', '16.0']

def get_emoji_string(codes_str):
    chars = []
    for code in codes_str.split():
        chars.append(chr(int(code, 16)))
    return ''.join(chars)

def process_version(version):
    print(f"Processing version {version}...")
    url = f"https://unicode.org/Public/emoji/{version}/emoji-test.txt"
    try:
        response = requests.get(url)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return

    text = response.text
    
    all_sequences = []
    tme_sequences = set()
    components = set()
    
    skin_tones = {0x1F3FB, 0x1F3FC, 0x1F3FD, 0x1F3FE, 0x1F3FF}
    
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        parts = line.split(';')
        if len(parts) < 2:
            continue
            
        codes_str = parts[0].strip()
        rest = parts[1].split('#')
        status = rest[0].strip()
        
        # In the original notebook, all items scraped from html were included.
        # emoji-list.html only has fully-qualified. component is needed for skin tones.
        if status not in ('fully-qualified', 'component'):
            continue
            
        emoji_str = get_emoji_string(codes_str)
        all_sequences.append(emoji_str)
        
        # Determine if it's a TME
        # A TME is any emoji that has a skin tone modifier, OR it's the base of one.
        # We can detect this if any code point is a skin tone.
        codes = [int(c, 16) for c in codes_str.split()]
        has_skin_tone = any(c in skin_tones for c in codes)
        if has_skin_tone:
            tme_sequences.add(emoji_str)
            # The base character is everything without the skin tone.
            base_codes = [c for c in codes if c not in skin_tones]
            base_str = ''.join(chr(c) for c in base_codes)
            if base_str:
                tme_sequences.add(base_str)
            
        if status == 'component':
            components.add(emoji_str)
            
    if not all_sequences:
        print(f"No sequences found for {version}.")
        return

    # To build possible_emoji, we decompose all strings into individual characters
    possible_emoji = set()
    for seq in all_sequences:
        for char in seq:
            possible_emoji.add(char)
            
    # Sort by length descending for regex
    all_sequences.sort(key=len, reverse=True)
    tme_list = list(tme_sequences)
    tme_list.sort(key=len, reverse=True)
    
    big_regex_pattern = '|'.join(re.escape(s) for s in all_sequences)
    tme_regex_pattern = '|'.join(re.escape(s) for s in tme_list)
    
    # Save
    out_dir = f"emoji_extractor/data/{version}"
    os.makedirs(out_dir, exist_ok=True)
    
    with open(f"{out_dir}/big_regex.txt", "w", encoding="utf-8") as f:
        f.write(big_regex_pattern)
        
    with open(f"{out_dir}/tme_regex.txt", "w", encoding="utf-8") as f:
        f.write(tme_regex_pattern)
        
    with open(f"{out_dir}/possible_emoji.json", "w", encoding="utf-8") as f:
        json.dump(list(possible_emoji), f, ensure_ascii=False)
        
    print(f"Version {version}: {len(all_sequences)} sequences, {len(tme_list)} TMEs, {len(possible_emoji)} chars.")

if __name__ == '__main__':
    for v in VERSIONS:
        process_version(v)
