"""Post-review correction from frozen result rows; no model calls or statistical refit."""
from pathlib import Path
import json,sys,base64,hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path(sys.argv[1]);src=root/'upgraded';out=root/'post_review';out.mkdir(exist_ok=True)
r=json.loads((src/'followup_results.json').read_text());cfg=json.loads((src/'followup_config.json').read_text())
t=pd.DataFrame(r['shortlist']);genes=cfg['prespecified']+cfg['selected_exploratory']
counts={c:int(t.query("gene=='VEGFA' and layer=='protein' and cohort==@c").iloc[0]['n']) for c in ['all_stage','stage_I_II']}
assert counts=={'all_stage':1,'stage_I_II':0}
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':140})
fig,axs=plt.subplots(1,2,figsize=(12,5))
for ax,l in zip(axs,['protein','rna']):
 for i,(cohort,label,color) in enumerate([('all_stage','All stages (72)','#0072B2'),('stage_I_II','Stage I/II (37)','#D55E00')]):
  z=t.query('cohort==@cohort and layer==@l').set_index('gene').loc[genes];x=z.mean_difference.where(z.status=='tested');ax.errorbar(x,np.arange(6)+(i-.5)*.2,xerr=[x-z.ci_low,z.ci_high-x],fmt='o',capsize=3,label=label,color=color)
 ax.set_yticks(range(6),genes);ax.invert_yaxis();ax.axvline(0,color='gray',ls=':');ax.set_title(l+' • paired mean and nominal 95% CI');ax.set_xlabel(cfg['scales'][l]+'\ntumor − normal');ax.legend(loc='lower right',fontsize=9)
 if l=='protein':ax.text(.98,2,f"VEGFA: n={counts['all_stage']} / {counts['stage_I_II']}; not tested",transform=ax.get_yaxis_transform(),ha='right',fontsize=9)
fig.suptitle('Original shortlist under stage restriction • corrected after review');fig.tight_layout();fig.savefig(out/'shortlist_comparison.png');plt.close(fig)
old='protein has one finite pair in each cohort';new='protein has one finite pair all-stage and zero early-stage'
notice='Post-review correction by the parent analyst: VEGFA protein n=1 all-stage / n=0 early-stage. The plot label is now generated from frozen result rows. No estimates were changed or refitted. Original benchmark artifacts, review scores and token totals remain unchanged.'
h=(src/'followup.html').read_text();assert old in h
h=h.replace(old,new).replace('<body>','<body><p style="padding:18px;background:#fff0d0"><strong>'+notice+'</strong></p>',1)
a=base64.b64encode((src/'followup_figures/shortlist_comparison.png').read_bytes()).decode();b=base64.b64encode((out/'shortlist_comparison.png').read_bytes()).decode();assert a in h;h=h.replace(a,b)
(out/'followup_corrected.html').write_text(h)
md=(src/'FOLLOWUP.md').read_text().replace(old,new).replace('(followup_figures/shortlist_comparison.png)','(shortlist_comparison.png)').replace('(followup_figures/effect_comparison.png)','(../upgraded/followup_figures/effect_comparison.png)');(out/'FOLLOWUP_corrected.md').write_text('> '+notice+'\n\n'+md)
(out/'memory_correction.json').write_text(json.dumps({'key':'stage_I_II_sensitivity','supersedes_interpretation_in':'../upgraded/followup_memory_append.json','correction':counts,'reason':'Original sensitivity summary omitted cohort qualification for VEGFA protein count. Use these cohort-specific counts when continuing. Frozen benchmark database is not modified.','attribution':'Parent analyst after independent artifact review; not human approval','source_sha256':hashlib.sha256((src/'followup_results.json').read_bytes()).hexdigest()},indent=2)+'\n')
(out/'README.md').write_text('# Post-review correction\n\n'+notice+'\n\nThe sensitivity memory export also needs cohort qualification; `memory_correction.json` is the continuation erratum. Treat it as required context before reusing that frozen summary. We preserve the original database and artifacts for benchmark audit.\n')
print(counts)
