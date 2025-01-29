import re
import pickle
import requests
from collections import defaultdict

def convert_code(original):
    codes = []

    for data in original.split(' '):
        c = f"\\U{int(data, 16):08x}"

        codes.append(c)
        
    return ''.join(codes).upper()

def shorten_name(name):
    for i in [": light skin tone", ": medium-light skin tone", ": medium skin tone", ": medium-dark skin tone", ": dark skin tone",
              ", light skin tone", ", medium-light skin tone", ", medium skin tone", ", medium-dark skin tone", ", dark skin tone"]:
        name = name.replace(i, '')

    return name
    

print('Loading latest Unicode data...')

raw_data = requests.get('https://unicode.org/Public/emoji/latest/emoji-test.txt')


print('\tDone.')

data = raw_data.content.decode().splitlines()

current_group = None
current_subgroup = None
version = None

name_to_codepoint = defaultdict(list)
allowed_emoji = set()
tme_names = set()


print('Processing...')
for line in data:
    if line == '':
        continue

    if line == '#EOF':
        break
        
    if line[0] != '#':
        codepoints = re.sub(r'\s+', ' ', line.split(';')[0].strip())

        emoji = ''.join([chr(int(c, 16)) for c in codepoints.split()])
                        
        status = line.split(';')[1].split('#')[0].strip()

        name = re.split(r' E\d+\.\d+ ', line)[1].strip()

        if status != 'component':
            allowed_emoji.add(emoji)
            
            c = convert_code(codepoints)

            name_to_codepoint[name.split(':')[0]].append(c)

            if 'skin tone' in name:
                tme_names.add(name.split(':')[0])

            continue

    if line.startswith('# Version:'):
        version = line.split(' ')[-1]

codepoint_data = sorted([i for j in name_to_codepoint.values() for i in j], key=lambda x: len(x), reverse=True)

tme_codepoints = []

for tme in tme_names:
    tme_codepoints.extend(name_to_codepoint[tme])

tme_codepoints = sorted(tme_codepoints, key=lambda x: len(x), reverse=True)

print('\tDone.')
print(f'\tFound {len(codepoint_data)} emoji codepoint sequences.')

big_regex = re.compile('|'.join(codepoint_data), re.UNICODE)
tme_regex = re.compile('|'.join(tme_codepoints), re.UNICODE)


print('Saving to disk...')
with open('../emoji_extractor/data/big_regex.pkl', 'wb') as f:
    pickle.dump(big_regex, f)

with open('../emoji_extractor/data/possible_emoji.pkl', 'wb') as f:
    pickle.dump(allowed_emoji, f)

with open('../emoji_extractor/data/tme_regex.pkl', 'wb') as f:
    pickle.dump(tme_regex, f)

print('\tDone.')