from pathlib import Path
from pprint import pprint
import generate_nanonis_tcp as gen

commands = gen.parse_pdf(Path('TCPProtocol_SPM.pdf'), start_page=37)
for cmd_name, payload in commands.items():
    for key in payload['respTypes']:
        if 'Signal name size' in key:
            print(cmd_name)
            pprint(payload['respTypes'])
            raise SystemExit
