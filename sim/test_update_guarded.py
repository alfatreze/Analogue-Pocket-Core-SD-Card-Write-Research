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
import update_guarded as update


def digest(data):return hashlib.sha256(data).hexdigest()


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)/'project';self.card=Path(self.temp.name)/'card'
        self.root.mkdir();self.card.mkdir()
        self.patches=[patch.object(update,'VERIFIED_RUN','CONNECTED-006-TEST'),patch.object(update,'BUILD','guarded06'),patch.object(update,'ROOT',self.root),patch.object(update,'CARD',self.card),
                      patch.object(update,'EVIDENCE',self.root/'work/evidence/update-guarded06'),
                      patch.object(update.install,'CARD',self.card),patch.object(update.install,'identity',return_value={})]
        for p in self.patches:p.start()
        self.old=update.CORE+'/core.json';self.bitstream=update.CORE+'/bitstream.rbf_r'
        self.put(self.card/self.old,b'old metadata');self.put(self.card/self.bitstream,b'old qualified bitstream')
        self.put(self.card/'Platforms/cardwrite.json',b'unchanged platform')
        self.put(self.card/'Assets/cardwrite/alfatreze.CARDWRITE02/write64.bin',b'prior physical result')
        self.put(self.card/'Assets/cardwrite/alfatreze.CARDWRITE02/batch-b003.bin',b'prior batch result')
        prior_paths=['Assets/cardwrite/alfatreze.CARDWRITE02/write64.bin','Assets/cardwrite/alfatreze.CARDWRITE02/batch-b003.bin']
        self.put(self.root/'work/evidence/runs/STRESS-004-COLD-REPEAT09/after.json',json.dumps({p:{'sha256':digest((self.card/p).read_bytes())} for p in prior_paths}).encode())
        self.put(self.card/'Assets/cardwrite/alfatreze.CARDWRITE02/stress-b004.bin',b'prior stress result')
        self.put(self.card/'unrelated.bin',b'leave me unchanged')
        self.put(self.card/'System/corelist_cache.bin',b'old cache')
        for build in ('recovery05','guarded06'):
            package=self.root/'work/packages'/build
            self.put(package/self.old,b'old metadata' if build=='recovery05' else b'new B006 metadata')
            self.put(package/self.bitstream,b'old qualified bitstream' if build=='recovery05' else b'new qualified bitstream')
            self.put(package/'Platforms/cardwrite.json',b'unchanged platform')
            manifest={'provenance':{'minimum_reported_slack_ns':1},'files':{p.relative_to(package).as_posix():digest(p.read_bytes()) for p in package.rglob('*') if p.is_file()}}
            self.put(package.parent/(build+'-manifest.json'),json.dumps(manifest).encode())
        self.put(self.root/'work/evidence/custom-build-audit-guarded06.json',b'{"minimum_reported_slack_ns":1}')
        self.put(self.root/'work/evidence/custom-build-audit-recovery05.json',b'{"minimum_reported_slack_ns":1}')
        self.put(self.root/'work/build/recovery05/source.v',b'frozen sources')
        self.put(self.root/'work/build/recovery05-manifest.json',json.dumps({'files':{'source.v':digest(b'frozen sources')}}).encode())
        self.put(self.root/'work/fpga/recovery05-s1/core.sof',b'old SOF')
        import recovery
        data=[]
        for asset,g in zip(update.ASSETS,(649,648)):
            b=bytearray(recovery.fixture());b[512:1024]=recovery.record(g);self.put(self.card/asset,b);data.append(bytes(b))
        self.put(self.root/'work/evidence/b005-connected-summary.json',b'{"pass":true}')
        self.put(self.root/'work/evidence/b005-connected-campaign.json',b'{"state":"completed"}')
        campaign=self.root/'work/evidence/b006-connected-campaign.json';self.put(campaign,b'{"state":"completed"}')
        summary=self.root/'work/evidence/b006-connected-summary.json'
        self.put(summary,json.dumps({'pass':True,'campaign_sha256':digest(campaign.read_bytes()),'final_expected_files':recovery.verify_files(*data)}).encode())
        trial=self.root/'work/evidence/runs/CONNECTED-006-TEST'
        result={'pass':True,'exact_connected_model_pass':True,'stable_during_collection':True,'experiment_build':'B006','connected_summary_sha256':digest(summary.read_bytes())}
        self.put(trial/'result.json',json.dumps(result).encode());self.put(trial/'after.json',json.dumps(update.install.snapshot()).encode())
        for asset in update.ASSETS:self.put(trial/Path(asset).name,(self.card/asset).read_bytes())
        self.put(self.root/'work/evidence/runs/STRESS-004-COLD-REPEAT09/after.json',json.dumps(update.install.snapshot()).encode())

    def tearDown(self):
        for p in reversed(self.patches):p.stop()
        self.temp.cleanup()

    def put(self,path,data):path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)

    def test_verified_update_and_preservation(self):
        plan=update.plan();update.apply(plan)
        self.assertEqual((self.card/self.old).read_bytes(),b'new B006 metadata')
        self.assertEqual((self.card/'unrelated.bin').read_bytes(),b'leave me unchanged')
        self.assertEqual((self.card/'Assets/cardwrite/alfatreze.CARDWRITE02/write64.bin').read_bytes(),b'prior physical result')
        self.assertEqual((self.card/'Assets/cardwrite/alfatreze.CARDWRITE02/stress-b004.bin').read_bytes(),b'prior stress result')
        for asset in update.ASSETS:self.assertEqual((self.card/asset).read_bytes(),(update.EVIDENCE/'backup'/asset).read_bytes())
        self.assertEqual((update.EVIDENCE/'backup'/self.bitstream).read_bytes(),b'old qualified bitstream')
        self.assertFalse((self.card/'System/corelist_cache.bin').exists())
        self.assertEqual(json.loads((update.EVIDENCE/'journal.json').read_text())['state'],'completed')

    def test_changed_unrelated_file_rejected(self):
        self.put(self.card/'unrelated.bin',b'changed')
        with self.assertRaises(ValueError):update.plan()

    def test_new_unrelated_file_rejected(self):
        self.put(self.card/'unexpected.bin',b'new')
        with self.assertRaises(ValueError):update.plan()

    def test_changed_prior_stress_rejected(self):
        self.put(self.card/'Assets/cardwrite/alfatreze.CARDWRITE02/stress-b004.bin',b'changed')
        with self.assertRaises(ValueError):update.plan()

    def test_second_scratch_also_rejected(self):
        self.put(self.card/update.ASSETS[1],b'old result')
        with self.assertRaises(ValueError):update.plan()

    def test_changed_prior_output_rejected(self):
        self.put(self.card/'Assets/cardwrite/alfatreze.CARDWRITE02/batch-b003.bin',b'changed result')
        with self.assertRaises(ValueError):update.plan()

    def test_modified_active_core_rejected(self):
        self.put(self.card/self.bitstream,b'unexpected image')
        with self.assertRaises(ValueError):update.plan()

    def test_prior_batch_not_reset(self):
        self.put(self.card/update.ASSETS[0],b'prior batch result')
        with self.assertRaises(ValueError):update.plan()

    def test_changed_package_rejected(self):
        self.put(self.root/'work/packages/guarded06'/self.old,b'modified metadata')
        with self.assertRaises(ValueError):update.plan()

    def test_path_traversal_rejected(self):
        path=self.root/'work/packages/guarded06-manifest.json'
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


    def test_asset_fixture_in_package_refused(self):
        package=self.root/'work/packages/guarded06';asset=update.ASSETS[0];self.put(package/asset,bytes([165])*8192)
        manifest=package.parent/'guarded06-manifest.json';d=json.loads(manifest.read_text());d['files'][asset]=digest((package/asset).read_bytes());manifest.write_text(json.dumps(d))
        with self.assertRaises(ValueError):update.plan()

    def test_missing_verified_run_refused(self):
        with patch.object(update,'VERIFIED_RUN',None),self.assertRaises(ValueError):update.plan()

    def test_failed_remount_gate_refused(self):
        p=self.root/'work/evidence/runs/CONNECTED-006-TEST/result.json';d=json.loads(p.read_text());d['pass']=False;p.write_text(json.dumps(d))
        with self.assertRaises(ValueError):update.plan()

    def test_altered_host_raw_backup_refused(self):
        self.put(self.root/'work/evidence/runs/CONNECTED-006-TEST'/Path(update.ASSETS[0]).name,b'changed')
        with self.assertRaises(ValueError):update.plan()

if __name__=='__main__':unittest.main()
