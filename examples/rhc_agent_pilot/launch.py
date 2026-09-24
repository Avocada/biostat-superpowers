from pathlib import Path
import subprocess,os,time,json,signal,sys
root=Path(__file__).resolve().parent
arm=sys.argv[1];phase=sys.argv[2] if len(sys.argv)>2 else 'initial'
folder=root/arm
cmd=['/Applications/ChatGPT.app/Contents/Resources/codex','exec','--ignore-user-config','--ephemeral','--skip-git-repo-check','--approve-for-me','-C',str(folder),'-m','gpt-6-astra','-c','model_reasoning_effort="medium"','-c','sandbox_workspace_write.network_access=true','-c','web_search="disabled"','-c','skills.config=[{path="/Users/amiee/.codex/skills/biostat-workflow",enabled=false}]','--json','-o',str(folder/f'final_{phase}.md'),'-']
if arm=='upgraded':
    cmd[-1:-1]=['-c','mcp_servers.biostat.command="/Users/amiee/Projects_code/biostat-superpowers/.venv/bin/python"','-c',f'mcp_servers.biostat.args=["-m","biostat_mcp.server","--artifact-dir","{folder}/mcp_artifacts","--input-dir","{folder}/input"]','-c','mcp_servers.biostat.env.PYTHONPATH="/Users/amiee/Projects_code/biostat-superpowers"','-c','mcp_servers.biostat.startup_timeout_sec=30','-c','mcp_servers.biostat.tool_timeout_sec=90']
prompt=(root/f'{arm}_{phase}_prompt.txt').read_text()
start=time.time()
with (root/f'{arm}_{phase}.jsonl').open('w') as out,(root/f'{arm}_{phase}.stderr').open('w') as err:
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=out,stderr=err,text=True,start_new_session=True,env={**os.environ,'MPLCONFIGDIR':str(folder/'.mplcache'),'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1'})
    timed_out=False
    try:proc.communicate(prompt,timeout=600)
    except subprocess.TimeoutExpired:
        timed_out=True;os.killpg(proc.pid,signal.SIGTERM)
        try:proc.wait(timeout=15)
        except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
record={'arm':arm,'phase':phase,'seconds':time.time()-start,'returncode':proc.returncode,'timeout':timed_out,'command':cmd}
(root/f'{arm}_{phase}_execution.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record))
