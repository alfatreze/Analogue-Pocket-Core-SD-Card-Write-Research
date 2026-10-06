#!/usr/bin/env python3
"""Exercise B007R5 update planning against temporary card/package fixtures."""
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
spec = importlib.util.spec_from_file_location('update_powercut', ROOT/'tools/update_powercut.py')
update = importlib.util.module_from_spec(spec);spec.loader.exec_module(update)
import install


def digest(data):return hashlib.sha256(data).hexdigest()


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)/'repo';self.card=Path(self.tmp.name)/'CARDWRITE';self.card.mkdir();self.root.mkdir()
        self.evidence=self.root/'work/evidence/update-powercut07r5'
        self.patches=[patch.object(update,'ROOT',self.root),patch.object(update,'CARD',self.card),
            patch.object(update,'EVIDENCE',self.evidence),patch.object(install,'ROOT',self.root),
            patch.object(install,'CARD',self.card),patch.object(install,'identity',return_value={'VolumeUUID':install.UUID}),
            patch.object(install,'safe',lambda path,base: None)]
        for p in self.patches:p.start()
        self.stage=self.root/'work/build/powercut07r5';self.stage.mkdir(parents=True)
        self.package=self.root/'work/packages/powercut07r5';self.package.mkdir(parents=True)
        self.host=self.root/'work/evidence/runs'/update.HOST_RUN;self.host.mkdir(parents=True)
        self.fixture_files={
            'Cores/alfatreze.CARDWRITE02/core.json':(b'B006 core',b'B007 core'),
            'Cores/alfatreze.CARDWRITE02/bitstream.rbf_r':(b'B006 bitstream',b'B007 bitstream'),
            'Cores/alfatreze.CARDWRITE02/info.txt':(b'B006 info',b'B007 info'),
            'Platforms/cardwrite.json':(b'platform',b'platform'),
            update.PRESERVE[0]:(b'write64',None),update.PRESERVE[1]:(b'batch',None),
            update.PRESERVE[2]:(b'stress',None),update.PRESERVE[3]:(b'partial A',None),
            update.PRESERVE[4]:(b'valid B',None),
            'System/corelist_cache.bin':(b'cache',None),
        }
        baseline={}
        b006_core_files={}
        for relative,(old,new) in self.fixture_files.items():
            path=self.card/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(old)
            baseline[relative]={'size':len(old),'sha256':digest(old)}
            if relative.startswith(update.CORE+'/'):b006_core_files[relative]=digest(old)
            if new is not None:
                target=self.package/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(new)
        scratch_data=bytes([0xA5])*262144
        scratch=self.package/update.SCRATCH;scratch.parent.mkdir(parents=True,exist_ok=True);scratch.write_bytes(scratch_data)
        new_files={}
        for relative,(old,new) in self.fixture_files.items():
            if new is not None:new_files[relative]=digest(new)
        new_files[update.SCRATCH]=digest(scratch_data)
        stage_relative='rtl.v';stage_file=self.stage/stage_relative;stage_file.write_bytes(b'frozen')
        stage_manifest={'files':{stage_relative:digest(b'frozen')}}
        (self.root/'work/build/powercut07r5-manifest.json').write_text(json.dumps(stage_manifest))
        audit={'minimum_reported_slack_ns':1,'compile_source_manifest_sha256':digest(json.dumps(stage_manifest).encode())}
        # Match the exact bytes used by checked_manifest's SHA check.
        manifest_path=self.root/'work/build/powercut07r5-manifest.json';audit['compile_source_manifest_sha256']=digest(manifest_path.read_bytes())
        audit_path=self.root/'work/evidence/custom-build-audit-powercut07r5.json';audit_path.parent.mkdir(parents=True,exist_ok=True);audit_path.write_text(json.dumps(audit))
        (self.package.parent/'powercut07r5-manifest.json').write_text(json.dumps({'provenance':audit,'files':new_files}))
        (self.root/'work/packages/guarded06-manifest.json').write_text(json.dumps({'files':b006_core_files}))
        (self.root/'work/evidence/b007-simulation-summary.json').write_text(json.dumps({'pass':True}))
        (self.root/'work/evidence/b007-display-review.json').write_text(json.dumps({'pass':True}))
        self.host_result={'pass':True,'stable_during_collection':True,'test_id':update.HOST_RUN}
        (self.host/'result.json').write_text(json.dumps(self.host_result))
        self.host_summary={'pass':True,'stable_during_collection':True,'volume_uuid':install.UUID,
            'actual_sha256':[baseline[update.PRESERVE[-2]]['sha256'],baseline[update.PRESERVE[-1]]['sha256']]}
        (self.root/'work/evidence/b006-power-cycle-prefix-host-summary.json').write_text(json.dumps(self.host_summary))
        (self.root/'work/evidence/b006-power-cycle-prefix-preparation.json').write_text(json.dumps({'pass':True}))
        (self.host/'after.json').write_text(json.dumps(baseline))
        self.baseline=baseline
        # Enough exact B006 files for the immutable local archive step.
        archive_inputs=[self.root/'work/build/guarded06',self.root/'work/build/guarded06-manifest.json',
            self.root/'work/fpga/guarded06-s1',self.root/'work/packages/guarded06',
            self.root/'work/packages/guarded06-manifest.json',self.root/'work/evidence/custom-build-audit-guarded06.json',
            self.root/'work/evidence/b006-final-card-verification.json',self.root/'work/evidence/b006-post-install-64-save-summary.json',
            self.root/'work/evidence/b006-post-install-64-remount-summary.json',self.root/'work/evidence/b006-power-cycle-prefix-jtag-summary.json',
            self.root/'work/evidence/b006-power-cycle-prefix-host-summary.json',self.root/'work/evidence/b006-power-cycle-prefix-preparation.json',
            self.host]
        for path in archive_inputs:
            if path.suffix:
                path.parent.mkdir(parents=True,exist_ok=True)
                if not path.exists():path.write_bytes(b'archive')
            else:
                path.mkdir(parents=True,exist_ok=True)
                (path/'fixture').write_bytes(b'archive')

    def tearDown(self):
        for p in reversed(self.patches):p.stop()
        self.tmp.cleanup()

    def test_dry_run_plans_exact_scratch_create_and_core_replacements(self):
        p=update.plan()
        actions={x['path']:x['action'] for x in p['package_files']}
        self.assertEqual(actions[update.SCRATCH],'create')
        self.assertEqual(actions[update.CORE+'/core.json'],'replace')
        self.assertEqual(actions['Platforms/cardwrite.json'],'identical')
        self.assertEqual(len(p['preserve']),5)

    def test_rejects_existing_scratch_and_stale_card_inventory(self):
        (self.card/update.SCRATCH).parent.mkdir(parents=True,exist_ok=True)
        (self.card/update.SCRATCH).write_bytes(b'old')
        with self.assertRaisesRegex(ValueError,'differs from the latest'):
            update.plan()
        (self.card/update.SCRATCH).unlink()
        with patch.object(install,'snapshot',return_value={**self.baseline,update.SCRATCH:{'size':3,'sha256':digest(b'old')}}):
            with self.assertRaisesRegex(ValueError,'differs from the latest'):
                update.plan()

    def test_rejects_unexpected_package_path_and_mutated_fixture(self):
        manifest_path=self.package.parent/'powercut07r5-manifest.json';manifest=json.loads(manifest_path.read_text())
        manifest['files']['Assets/other/unexpected.bin']=digest(b'x');manifest_path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError,'Unexpected B007R5 package path'):
            update.plan()

    def test_apply_preserves_all_old_outputs_and_records_exact_changes(self):
        # Use the actual temporary tree for each identity-checked snapshot.
        def snapshot():
            result={}
            for p in self.card.rglob('*'):
                if p.is_file():result[p.relative_to(self.card).as_posix()]={'size':p.stat().st_size,'sha256':digest(p.read_bytes())}
            return result
        with patch.object(install,'snapshot',side_effect=snapshot):
            plan=update.plan();update.apply(plan)
        after=snapshot()
        for item in plan['preserve']:self.assertEqual(after[item['path']]['sha256'],item['sha256'])
        scratch_plan=next(item for item in plan['package_files'] if item['path']==update.SCRATCH)
        self.assertEqual(after[update.SCRATCH]['sha256'],scratch_plan['sha256'])
        journal=json.loads((self.evidence/'journal.json').read_text())
        self.assertEqual(journal['state'],'completed')
        self.assertEqual(journal['unexpected_changes'],[])


if __name__=='__main__':unittest.main()
