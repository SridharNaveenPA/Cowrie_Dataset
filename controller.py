# controller.py
# Updated skeleton with Cowrie session extraction support.
# NOTE: Replace COWRIE_JSON_LOG with your installation path.

import json, os, time
from datetime import datetime
import paramiko

HOST="127.0.0.1"
PORT=2222
USERNAME="root"
PASSWORD="password"
COWRIE_JSON_LOG="/home/kali/cowrie/var/log/cowrie/cowrie.json"

SCENARIOS={
"1":{"name":"Credential Discovery","file":"credential_discovery.json"},
"2":{"name":"Privilege Escalation","file":"privilege_escalation.json"},
"3":{"name":"Persistence","file":"persistence.json"},
"4":{"name":"Lateral Movement","file":"lateral_movement.json"},
"5":{"name":"Ransomware Behaviour","file":"ransomware.json"},
}

print("="*70)
for k,v in SCENARIOS.items():
    print(f"[{k}] {v['name']}")
choice=input("Select scenario: ").strip()
if choice not in SCENARIOS: raise SystemExit("Invalid selection")

selected=SCENARIOS[choice]
with open(os.path.join("JSONs",selected["file"])) as f:
    scenario=json.load(f)

log_start=0
if os.path.exists(COWRIE_JSON_LOG):
    with open(COWRIE_JSON_LOG,"rb") as f:
        f.seek(0,2)
        log_start=f.tell()

client=paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST,port=PORT,username=USERNAME,password=PASSWORD,
               allow_agent=False,look_for_keys=False)
shell=client.invoke_shell()
time.sleep(2)
if shell.recv_ready(): shell.recv(65535)

execution_log={"scenario":scenario["scenario"],
               "start_time":str(datetime.now()),
               "phases":[]}

for phase in scenario["phases"]:
    p={"phase":phase["phase"],"commands":[]}
    print("="*60)
    print(phase["phase"])
    for cmdinfo in phase["commands"]:
        cmd=cmdinfo["command"]
        print(">>>",cmd)
        shell.send(cmd+"\n")
        time.sleep(2)
        out=""
        while shell.recv_ready():
            out+=shell.recv(65535).decode(errors="ignore")
        print(out)
        item=dict(cmdinfo)
        item["timestamp"]=str(datetime.now())
        item["output"]=out
        p["commands"].append(item)
    execution_log["phases"].append(p)

shell.send("exit\n")
time.sleep(1)
client.close()
time.sleep(2)

events=[]
session=None
if os.path.exists(COWRIE_JSON_LOG):
    with open(COWRIE_JSON_LOG,"rb") as f:
        f.seek(log_start)
        for line in f:
            try:
                e=json.loads(line.decode())
                events.append(e)
            except Exception:
                pass
    for e in events:
        if e.get("eventid")=="cowrie.session.connect":
            session=e.get("session")
            break
filtered=[e for e in events if session and e.get("session")==session]

execution_log["cowrie_session"]=session
execution_log["cowrie_events"]=len(filtered)
execution_log["end_time"]=str(datetime.now())

os.makedirs("execution_logs",exist_ok=True)
stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
base=scenario["scenario"].replace(" ","_").replace("/","_")

with open(f"execution_logs/{base}_{stamp}.json","w") as f:
    json.dump(execution_log,f,indent=4)

if session:
    with open(f"execution_logs/{base}_{stamp}_cowrie.json","w") as f:
        json.dump(filtered,f,indent=4)

print("Done.")
