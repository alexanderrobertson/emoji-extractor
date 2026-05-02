import os
import re
import json
import requests
import sys

def get_emoji_string(codes_str):
    chars = []
    for code in codes_str.split():
        chars.append(chr(int(code, 16)))
    return ''.join(chars)

def update_latest():
    url = "https://unicode.org/Public/emoji/latest/emoji-test.txt"
    try:
        response = requests.get(url)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        sys.exit(1)

    text = response.text
    
    # Parse version from header
    version_match = re.search(r"# Version:\s*([0-9.]+)", text)
    if not version_match:
        print("Could not find Version in the file header.")
        sys.exit(1)
        
    version = version_match.group(1)
    out_dir = f"emoji_extractor/data/{version}"
    
    if os.path.exists(out_dir):
        print(f"Version {version} is already up to date.")
        return False # No update needed
        
    print(f"New Unicode Emoji Version {version} detected. Updating...")
    
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
        
        if status not in ('fully-qualified', 'component'):
            continue
            
        emoji_str = get_emoji_string(codes_str)
        all_sequences.append(emoji_str)
        
        codes = [int(c, 16) for c in codes_str.split()]
        has_skin_tone = any(c in skin_tones for c in codes)
        if has_skin_tone:
            tme_sequences.add(emoji_str)
            base_codes = [c for c in codes if c not in skin_tones]
            base_str = ''.join(chr(c) for c in base_codes)
            if base_str:
                tme_sequences.add(base_str)
            
        if status == 'component':
            components.add(emoji_str)

    possible_emoji = set()
    for seq in all_sequences:
        for char in seq:
            possible_emoji.add(char)
            
    all_sequences.sort(key=len, reverse=True)
    tme_list = list(tme_sequences)
    tme_list.sort(key=len, reverse=True)
    
    big_regex_pattern = '|'.join(re.escape(s) for s in all_sequences)
    tme_regex_pattern = '|'.join(re.escape(s) for s in tme_list)
    
    # Save to specific version dir
    os.makedirs(out_dir, exist_ok=True)
    with open(f"{out_dir}/big_regex.txt", "w", encoding="utf-8") as f:
        f.write(big_regex_pattern)
    with open(f"{out_dir}/tme_regex.txt", "w", encoding="utf-8") as f:
        f.write(tme_regex_pattern)
    with open(f"{out_dir}/possible_emoji.json", "w", encoding="utf-8") as f:
        json.dump(list(possible_emoji), f, ensure_ascii=False)
        
    # Update default version in extract.py
    extract_py_path = "emoji_extractor/extract.py"
    with open(extract_py_path, "r", encoding="utf-8") as f:
        extract_content = f.read()
    
    extract_content = re.sub(
        r"DEFAULT_VERSION\s*=\s*['\"].*?['\"]",
        f"DEFAULT_VERSION = '{version}'",
        extract_content
    )
    
    with open(extract_py_path, "w", encoding="utf-8") as f:
        f.write(extract_content)
        
    # Update README.md
    readme_path = "README.md"
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            readme_content = f.read()
        match = re.search(r"Available versions: (.*)\.", readme_content)
        if match:
            versions_str = match.group(1)
            if f"`{version}`" not in versions_str:
                new_versions_str = f"{versions_str}, `{version}`"
                readme_content = readme_content.replace(match.group(0), f"Available versions: {new_versions_str}.")
                with open(readme_path, "w", encoding="utf-8") as f:
                    f.write(readme_content)
    print(f"Successfully updated to Version {version}.")
    # We write a github output variable to trigger a commit/release
    if "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"new_version={version}\n")
            f.write("updated=true\n")
            
    return True

if __name__ == '__main__':
    update_latest()
