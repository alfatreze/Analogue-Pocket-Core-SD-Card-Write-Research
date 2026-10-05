#!/usr/bin/env python3
"""Preserve/remount-check exact final connected model plus protected card contents."""
import argparse,json,sys
from pathlib import Path
import install,recovery,read_recovery_results as prior
ROOT=install.ROOT;ASSETS=prior.ASSETS
def collect(build,test_id,firmware,allow_stopped=False):
 prior.test_id(test_id);info=install.identity();folder=ROOT/'work/evidence/runs'/test_id
 if folder.exists():raise ValueError('Existing trial evidence; never overwrite')
 campaign_path=ROOT/'work/evidence'/(build.lower()+'-connected-resumed-campaign.json');summary_path=ROOT/'work/evidence'/(build.lower()+'-connected-resumed-summary.json')
 campaign=json.loads(campaign_path.read_text());stopped=False
 if build!='B006' or allow_stopped:raise ValueError('This collector requires completed resumed-baseline B006')
 if stopped:summary_path=ROOT/'work/evidence'/(build.lower()+'-connected-stopped-summary.json')
 summary=json.loads(summary_path.read_text())
 proof=summary.get('evidence_replay_pass',summary.get('pass',False)) if stopped else summary.get('pass',False)
 if (campaign['state']!='completed' and not stopped) or not proof or summary['campaign_sha256']!=install.sha(campaign_path):raise ValueError('Independently verified completed campaign or explicit stopped forensic prefix required')
 expected=campaign['expected_final_files']
 if expected!=summary['final_expected_files'] or not expected['pass']:raise ValueError('Final model mismatch')
 baseline_path=ROOT/'work/evidence/cleanup-b005/after.json';baseline=json.loads(baseline_path.read_text())
 after=install.snapshot();folder.mkdir(parents=True);data=[]
 for relative in ASSETS:
  source=install.CARD/relative;install.safe(source,install.CARD);content=source.read_bytes();copy=folder/source.name
  with copy.open('xb') as out:out.write(content)
  if install.sha(copy)!=after[relative]['sha256']:raise ValueError('Preserved raw file/snapshot differs')
  data.append(content)
 actual=recovery.verify_files(*data,expected_generation=expected['generation'],expect_generated=True)
 exact=actual==expected;changed=sorted(p for p in baseline if p not in ASSETS and baseline[p]!=after.get(p));added=sorted(set(after)-set(baseline))
 metadata=json.loads((install.CARD/'Cores/alfatreze.CARDWRITE02/core.json').read_text())['core']['metadata']
 result={'test_id':test_id,'experiment_build':build,'sd_metadata_version':metadata['version'],'firmware_reported':firmware,'volume':info,'file_verification':actual,'exact_connected_model_pass':exact,'campaign_sha256':install.sha(campaign_path),'connected_summary_sha256':install.sha(summary_path),'changed_or_missing_protected_files':changed,'new_files_for_review':added,'campaign_completed':not stopped,'file_evidence_pass':exact and actual['pass'] and not changed,'pass':not stopped and exact and actual['pass'] and not changed,'scope':'Physical host remount exact-size/full-byte/guard/model check; unrelated existing contents compared to B005 cleanup snapshot. Debug image and SD metadata recorded separately; exact power actions not inferred.'}
 latest=install.snapshot();result['stable_during_collection']=latest==after;result['pass']=result['pass'] and result['stable_during_collection'];result['file_evidence_pass']=result['file_evidence_pass'] and result['stable_during_collection'];install.identity()
 if latest!=after:(folder/'changed-during-collection.json').write_text(json.dumps(latest,indent=2)+'\n')
 (folder/'result.json').write_text(json.dumps(result,indent=2)+'\n');(folder/'after.json').write_text(json.dumps(after,indent=2)+'\n')
 return result
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',choices=('B005','B006'),default='B006');p.add_argument('--test-id',required=True);p.add_argument('--firmware',required=True);p.add_argument('--allow-stopped',action='store_true');args=p.parse_args();d=collect(args.build,args.test_id,args.firmware,args.allow_stopped);print(json.dumps(d,indent=2));return 0 if d['file_evidence_pass'] else 1
if __name__=='__main__':
 try:sys.exit(main())
 except (ValueError,OSError) as e:print(str(e),file=sys.stderr);raise SystemExit(1)
