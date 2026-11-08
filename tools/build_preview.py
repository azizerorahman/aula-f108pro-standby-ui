"""Build the offline preview from reviewed assets; no network or device access."""
from pathlib import Path
import base64, json
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'assets/manifest.json').read_text(encoding='utf-8'))
images={m['id']:'data:image/png;base64,'+base64.b64encode((ROOT/m['file']).read_bytes()).decode() for m in manifest['screens']}
template=(ROOT/'web/preview.template.html').read_text(encoding='utf-8')
text=template.replace('__SCREENS__',json.dumps(images)).replace('__META__',json.dumps(manifest['screens'],ensure_ascii=False)).replace('__EFFECTS__',(ROOT/'assets/effect_modes.json').read_text(encoding='utf-8'))
(ROOT/'docs/index.html').write_text(text,encoding='utf-8',newline='\n')
print('Built docs/index.html with %d states'%len(images))
