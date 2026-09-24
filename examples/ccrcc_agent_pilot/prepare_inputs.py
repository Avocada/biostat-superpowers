"""Recreate the frozen public input folder; requires openpyxl only for the clinical sheet.
Run: python prepare_inputs.py INPUT_DIRECTORY
Reads INPUT_MANIFEST.json and DATA_SOURCES.md beside this script; verifies every byte hash.
"""
import csv, hashlib, json, subprocess, sys
from pathlib import Path
import openpyxl
here=Path(__file__).resolve().parent;out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
manifest=json.loads((here/'INPUT_MANIFEST.json').read_text())
base='https://www.linkedomics.org/data_download/CPTAC-CCRCC/'
urls={n:base+n for n in ['HS_CPTAC_CCRCC_CLI.tsi','HS_CPTAC_CCRCC_proteome_Tumor.cct','HS_CPTAC_CCRCC_proteome_Normal.cct','HS_CPTAC_CCRCC_RNAseq_fpkm_log2_Tumor.cct','HS_CPTAC_CCRCC_RNAseq_fpkm_log2_Normal.cct']}
urls.update({'Clinical_Table_S1.xlsx':'https://byu.box.com/shared/static/q5bayxdevpwmq74chay5m0lrnc6vb71i.xlsx','cptac_metadata.csv.gz':'https://byu.box.com/shared/static/mf5uzbi0p1yldywbebrybavxdfg9vaqy.gz'})
for name,url in urls.items():
 p=out/name
 if not p.exists():
  tmp=out/(name+'.partial');subprocess.run(['curl','--fail','--silent','--show-error','--location','--max-time','120',url,'-o',str(tmp)],check=True);tmp.rename(p)
 if hashlib.sha256(p.read_bytes()).hexdigest()!=manifest['files'][name]['sha256']:raise RuntimeError('Source changed: '+name)
w=openpyxl.load_workbook(out/'Clinical_Table_S1.xlsx',data_only=True);rows=[row for row in w['ccrcc_clinical_characteristics'].values if row[0]];keep=[i for i,v in enumerate(rows[0]) if v]
with (out/'clinical_annotation.csv').open('w') as f:csv.writer(f).writerows([[row[i] for i in keep] for row in rows])
(out/'SOURCE.md').write_bytes((here/'DATA_SOURCES.md').read_bytes())
for name,record in manifest['files'].items():
 p=out/name
 if hashlib.sha256(p.read_bytes()).hexdigest()!=record['sha256']:raise RuntimeError('Input mismatch: '+name)
(out/'manifest.json').write_text(json.dumps(manifest,indent=2));print('Verified',manifest['input_fingerprint'])
