#!/usr/bin/env python3
"""Exercise the update guardrails against temporary fake card/project trees."""
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import update_stress as update


def digest(data):return hashlib.sha256(data).hexdigest()


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)/'project';self.card=Path(self.temp.name)/'card'
        self.root.mkdir();self.card.mkdir()
        self.patches=[patch.object(update,'BUILD','stress04r2'),patch.object(update,'ROOT',self.root),patch.object(update,'CARD',self.card),
                      patch.object(update,'EVIDENCE',self.root/'work/evidence/update-stress04r2'),
                      patch.object(update.install,'CARD',self.card),patch.object(update.install,'identity',return_value={})]
        for p in self.patches:p.start()
        self.old=update.CORE+'/core.json';self.bitstream=update.CORE+'/bitstream.rbf_r'
        self.put(self.card/self.old,b'old metadata');self.put(self.card/self.bitstream,b'old qualified bitstream')
        self.put(self.card/'Platforms/cardwrite.json',b'unchanged platform')
        self.put(self.card/'Assets/cardwrite/alfatreze.CARDWRITE02/write64.bin',b'prior physical result')
        self.put(self.card/'Assets/cardwrite/alfatreze.CARDWRITE02/batch-b003.bin',b'prior batch result')
        prior_paths=['Assets/cardwrite/alfatreze.CARDWRITE02/write64.bin','Assets/cardwrite/alfatreze.CARDWRITE02/batch-b003.bin']
        self.put(self.root/'work/evidence/runs/BATCH-003-COLD/after.json',json.dumps({p:{'sha256':digest((self.card/p).read_bytes())} for p in prior_paths}).encode())
        self.put(self.card/'unrelated.bin',b'leave me unchanged')
        self.put(self.card/'System/corelist_cache.bin',b'old cache')
        for build in ('batch03r2','stress04r2'):
            package=self.root/'work/packages'/build
            self.put(package/self.old,b'old metadata' if build=='batch03r2' else b'new B004 metadata')
            self.put(package/self.bitstream,b'old qualified bitstream' if build=='batch03r2' else b'new qualified bitstream')
            self.put(package/'Platforms/cardwrite.json',b'unchanged platform')
            if build=='stress04r2':self.put(package/update.ASSET,b'new guarded scratch')
            manifest={'provenance':{'minimum_reported_slack_ns':1},'files':{p.relative_to(package).as_posix():digest(p.read_bytes()) for p in package.rglob('*') if p.is_file()}}
            self.put(package.parent/(build+'-manifest.json'),json.dumps(manifest).encode())
        self.put(self.root/'work/evidence/custom-build-audit-stress04r2.json',b'{"minimum_reported_slack_ns":1}')
        self.put(self.root/'work/evidence/custom-build-audit-batch03r2.json',b'{}')
        self.put(self.root/'work/build/batch03r2/source.v',b'frozen sources')
        self.put(self.root/'work/build/batch03r2-manifest.json',json.dumps({'files':{'source.v':digest(b'frozen sources')}}).encode())
        self.put(self.root/'work/fpga/batch03r2-s1/core.sof',b'old SOF')

    def tearDown(self):
        for p in reversed(self.patches):p.stop()
        self.temp.cleanup()

    def put(self,path,data):path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)

    def test_verified_update_and_preservation(self):
        plan=update.plan();update.apply(plan)
        self.assertEqual((self.card/self.old).read_bytes(),b'new B004 metadata')
        self.assertEqual((self.card/'unrelated.bin').read_bytes(),b'leave me unchanged')
        self.assertEqual((self.card/'Assets/cardwrite/alfatreze.CARDWRITE02/write64.bin').read_bytes(),b'prior physical result')
        self.assertEqual((update.EVIDENCE/'backup'/self.bitstream).read_bytes(),b'old qualified bitstream')
        self.assertFalse((self.card/'System/corelist_cache.bin').exists())
        self.assertEqual(json.loads((update.EVIDENCE/'journal.json').read_text())['state'],'completed')

    def test_changed_prior_output_rejected(self):
        self.put(self.card/'Assets/cardwrite/alfatreze.CARDWRITE02/batch-b003.bin',b'changed result')
        with self.assertRaises(ValueError):update.plan()

    def test_modified_active_core_rejected(self):
        self.put(self.card/self.bitstream,b'unexpected image')
        with self.assertRaises(ValueError):update.plan()

    def test_prior_batch_not_reset(self):
        self.put(self.card/update.ASSET,b'prior batch result')
        with self.assertRaises(ValueError):update.plan()

    def test_changed_package_rejected(self):
        self.put(self.root/'work/packages/stress04r2'/self.old,b'modified metadata')
        with self.assertRaises(ValueError):update.plan()

    def test_path_traversal_rejected(self):
        path=self.root/'work/packages/stress04r2-manifest.json'
        value=json.loads(path.read_text())
        value['files'][update.CORE+'/../../escape.bin']=digest(b'escape')
        path.write_text(json.dumps(value))
        with self.assertRaises(ValueError):update.plan()

    def test_symlink_rejected(self):
        target=self.card/self.old;content=target.read_bytes();target.unlink()
        outside=Path(self.temp.name)/'outside';outside.write_bytes(content);target.symlink_to(outside)
        with self.assertRaises(ValueError):update.plan()

    def test_changed_plan_refused_before_mutation(self):
        plan=update.plan();self.put(self.card/'System/corelist_cache.bin',b'changed cache')
        with self.assertRaises(ValueError):update.apply(plan)
        self.assertEqual((self.card/self.old).read_bytes(),b'old metadata')


if __name__=='__main__':unittest.main()
