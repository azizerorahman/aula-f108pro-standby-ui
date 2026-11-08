"""Check public files for privacy leaks, image metadata, syntax and broken local links."""
from pathlib import Path
import ast, ipaddress, json, re, sys
from urllib.parse import unquote
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
SKIP={'.git','.venv','build','dist','private','__pycache__'}
files=[p for p in ROOT.rglob('*') if p.is_file() and not any(a in SKIP or a.startswith('.venv') for a in p.relative_to(ROOT).parts)]
errors=[]
text_extensions={'.md','.py','.ps1','.cs','.json','.html','.s','.txt','.yml','.yaml','.svg'}
# Values are assembled to avoid mistaking the detector's own source for a leak.
bad_path=re.compile(r'[A-Za-z]:'+re.escape(chr(92))+r'(?:Users|projects)'+re.escape(chr(92)),re.I)
private_id=re.compile(r'\bDESKTOP'+r'-[A-Z0-9]{5,}\b|HID'+re.escape(chr(92))+r'VID_[^\s]+&[0-9a-f]{8}&',re.I)
ipv4=re.compile(r'(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])')
for p in files:
    rel=p.relative_to(ROOT).as_posix()
    if p.suffix.lower() in {'.bin','.hex','.exe','.mp4','.mov','.pem','.key','.pfx','.zip'}:
        errors.append(rel+': forbidden binary/private artifact')
    if p.suffix=='.py':
        try:ast.parse(p.read_text(encoding='utf-8'))
        except SyntaxError:errors.append(rel+': Python syntax error')
    if p.suffix.lower() in text_extensions or p.name in {'LICENSE','.gitignore','.gitattributes','.editorconfig'}:
        text=p.read_text(encoding='utf-8')
        if bad_path.search(text) or private_id.search(text):errors.append(rel+': private host/path identifier')
        for value in ipv4.findall(text):
            try:
                addr=ipaddress.ip_address(value)
                if addr.is_private and not addr.is_loopback:errors.append(rel+': local network address')
            except ValueError:pass
        if re.search(r'(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----)',text):
            errors.append(rel+': probable credential')
        if p.suffix=='.md':
            for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',text):
                if re.match(r'(?:https?:|mailto:|#)',target):continue
                target=unquote(target.split('#')[0])
                if target and not (p.parent/target).exists():errors.append(rel+': broken relative link '+target)
    if p.suffix.lower()=='.png':
        im=Image.open(p)
        if im.getexif() or any(k in im.info for k in ['exif','comment','Description','Author','Software']):
            errors.append(rel+': embedded image metadata')
if errors:
    print('\n'.join(errors));sys.exit(1)
print(json.dumps({'public_files_checked':len(files),'privacy_findings':0,'syntax_and_local_links':'passed','device_opened':False}))
