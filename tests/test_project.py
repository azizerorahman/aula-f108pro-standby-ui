from pathlib import Path
import hashlib, importlib.util, json, struct, subprocess, sys, tempfile, unittest
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from standby_ui.rgb565 import encode, decode

class ProjectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=json.loads((ROOT/'assets/manifest.json').read_text(encoding='utf-8'))
        cls.layout=json.loads((ROOT/'assets/graphics/layout.json').read_text())
        cls.spi=encode(Image.open(ROOT/cls.layout['atlas']))[:cls.layout['bytes']]
        if not (ROOT/'build/rendered/manifest.json').exists():
            subprocess.run([sys.executable,str(ROOT/'tools/render_ui.py')],check=True,cwd=ROOT)

    def test_native_assets_and_integrity(self):
        screens=self.manifest['screens']
        self.assertEqual(len(screens),134)
        self.assertEqual(len({m['id'] for m in screens}),134)
        for m in screens:
            with self.subTest(screen=m['id']):
                p=ROOT/m['file'];im=Image.open(p)
                self.assertEqual(im.size,(240,135))
                self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),m['sha256'])
                self.assertEqual(decode(encode(im),240,135).tobytes(),im.tobytes())

    def test_portable_renderer_matches_reviewed_pixels(self):
        for m in self.manifest['screens']:
            with self.subTest(screen=m['id']):
                a=Image.open(ROOT/m['file'])
                b=Image.open(ROOT/'build/rendered/screens'/Path(m['file']).name)
                self.assertEqual(a.tobytes(),b.tobytes())

    def test_graphics_hash_boundaries_and_active_allocations(self):
        self.assertEqual(hashlib.sha256(self.spi).hexdigest(),self.layout['sha256'])
        self.assertEqual(len(self.spi)//4096,1807)
        self.assertEqual(len(self.spi)%4096,0)
        self.assertLess(len(self.spi),0x740000)
        lookup={m['id']:m for m in self.manifest['screens']}
        for entry in self.layout['screens']:
            with self.subTest(screen=entry['id']):
                x,y,w,h=entry['rect'];address=entry['address']
                self.assertGreaterEqual(address,0)
                self.assertLessEqual(address+w*h*2,len(self.spi))
                im=Image.open(ROOT/lookup[entry['id']]['file'])
                self.assertEqual(encode(im.crop((x,y,x+w,y+h))),self.spi[address:address+w*h*2])

    def test_native_effect_mapping(self):
        modes=json.loads((ROOT/'assets/effect_modes.json').read_text(encoding='utf-8'))
        expected=['Static','SingleOn','SingleOff','Glittering','Falling','Colourful','Breath','Spectrum','Outward','Scrolling','Rolling','Rotating','Explode','Launch','Ripples','Flowing','Pulsating','Tilt','Shuttle','LED Off']
        self.assertEqual([m['en'] for m in modes],expected)
        for i,m in enumerate(modes):
            self.assertEqual(m['native_menu_mode'],i)
            self.assertEqual(m['host_protocol_mode'],i+1 if i<19 else 0)

    def test_patch_bounds_and_reference_identity(self):
        spec=json.loads((ROOT/'firmware/patches.json').read_text())
        last=0
        for p in spec['patches']:
            before=bytes.fromhex(p['expected_hex']);after=bytes.fromhex(p['data_hex'])
            self.assertEqual(len(before),len(after));self.assertGreaterEqual(p['offset'],last)
            last=p['offset']+len(after)
            self.assertLessEqual(last,spec['base']['size'])
        self.assertEqual(spec['output']['sum16_le'],0x2bef)
        self.assertEqual(spec['output']['sha256'],'4383291939280af6d30fc962cdf60cf64d531ae10dcd56c2a99ed7ba9dd4a62b')

    def test_builder_rejects_unknown_base_before_output(self):
        path=ROOT/'tools/build_firmware.py'
        spec=importlib.util.spec_from_file_location('public_builder',path)
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp)/'wrong.bin';base.write_bytes(bytes(262144));out=Path(temp)/'output'
            with self.assertRaisesRegex(ValueError,'Unsupported stock'):
                mod.build(base,out)
            self.assertFalse(out.exists())

    def test_all_clock_times_fit(self):
        from standby_ui import clock
        self.assertLessEqual(max(clock.time_width(h,m) for h in range(24) for m in range(60)),220)
        self.assertEqual(clock.HERO_EN.size,(240,135))
        self.assertEqual(clock.HERO_CN.size,(240,135))

if __name__=='__main__':
    unittest.main()
