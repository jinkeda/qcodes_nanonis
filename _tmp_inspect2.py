from pathlib import Path
import json
import generate_nanonis_tcp as gen

pdf = Path('TCPProtocol_SPM.pdf')
commands = gen.parse_pdf(pdf, start_page=37)
with Path('nanonis_tcp.json').open('r', encoding='utf-8') as f:
    existing = json.load(f)
commands = gen.merge_with_existing(commands, existing)
for cmd_name, payload in commands.items():
    for key in payload['respTypes']:
        if 'Signal name size' in key:
            print('CMD', cmd_name, key)
    for key in payload['argTypes']:
        if 'Signal name size' in key:
            print('ARG', cmd_name, key)
