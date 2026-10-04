"""Host protection/integrity checks; no real-card writes."""
import importlib.util
import tempfile
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('lab', ROOT / 'tools/lab.py')
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)


class OracleTests(unittest.TestCase):
    def test_hardware_dump_against_independent_byte_oracle(self):
        for generation in (1, 2):
            lines = (ROOT / f'work/sim/generation-{generation}.hex').read_text().splitlines()
            transferred = b''.join(bytes.fromhex(line) for line in lines)
            self.assertEqual(transferred, lab.record(generation))

    def test_format_distinguishes_corruption_truncation_and_endianness(self):
        expected = lab.record(1)
        samples = [expected, expected[:-1], expected+b'\0', lab.record(2),
                   b''.join(expected[i:i+4][::-1] for i in range(0,64,4))]
        for index in (0, 8, 24, 63):
            bad = bytearray(expected)
            bad[index] ^= 1
            samples.append(bytes(bad))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'readback.bin'
            for index, sample in enumerate(samples):
                path.write_bytes(sample)
                run = subprocess.run([sys.executable,str(ROOT/'tools/lab.py'),'verify',str(path),'--generation','1'],capture_output=True)
                self.assertEqual(run.returncode, 0 if index == 0 else 1, run.stdout)

    def test_official_control_oracle_accepts_first_image_and_rejects_changed_file(self):
        data=(ROOT/'vendor/official-targetdata/dist/assets/ex_image_all.bin').read_bytes()[:184320]
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'saved.bin'
            for index,sample in enumerate((data,data[:-4],bytes(184320))):
                path.write_bytes(sample)
                run=subprocess.run([sys.executable,str(ROOT/'tools/lab.py'),'verify-control',str(path)],capture_output=True)
                self.assertEqual(run.returncode,0 if index==0 else 1,run.stdout)

    def test_fixture_cannot_write_outside_project_work(self):
        with self.assertRaises(ValueError):
            lab.local_output('/Volumes/ANY_CARD/write.bin')
        with self.assertRaises(ValueError):
            lab.local_output('work/../../another-project.bin')

    def test_manifest_records_protected_bytes_and_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            protected = root / 'music.mp3'
            protected.write_bytes(b'synthetic music')
            before = lab.file_manifest(root)
            protected.write_bytes(b'changed')
            self.assertNotEqual(before['files'], lab.file_manifest(root)['files'])
            (root / 'alias').symlink_to(protected)
            with self.assertRaises(ValueError):
                lab.file_manifest(root)


if __name__ == '__main__':
    unittest.main(verbosity=2)
