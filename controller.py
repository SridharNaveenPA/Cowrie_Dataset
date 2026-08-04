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
COWRIE_JSON_LOG="/home/cowrie/cowrie/var/log/cowrie/cowrie.json"

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
print(f"[*] Cowrie log offset : {log_start}")
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

print(f"[*] Cowrie log size : {os.path.getsize(COWRIE_JSON_LOG)}")

# =====================================================
# Extract Cowrie Session Logs
# =====================================================

print("\n[*] Extracting Cowrie logs...")

events = []
filtered = []
session = None

if not os.path.exists(COWRIE_JSON_LOG):
    print("[!] Cowrie log file not found!")
else:

    # Read only the newly-added portion of cowrie.json
    with open(COWRIE_JSON_LOG, "r", encoding="utf-8", errors="ignore") as f:

        f.seek(log_start)

        for line in f:

            line = line.strip()

            if not line:
                continue

            try:
                event = json.loads(line)
                events.append(event)

            except json.JSONDecodeError:
                continue

    print(f"[+] New Cowrie events read : {len(events)}")

    # -------------------------------------------------
    # Find our session
    # -------------------------------------------------

    for event in events:

        event_name = event.get("eventid") or event.get("event")

        if event_name == "cowrie.session.connect":

            session = event.get("session")

            print(f"[+] Session Found : {session}")

            break

    if session is None:

        print("[!] No Cowrie session found.")

    else:

        # Extract only events from this session

        filtered = [

            e for e in events

            if e.get("session") == session

        ]

        print(f"[+] Session Events : {len(filtered)}")

execution_log["cowrie_session"] = session
execution_log["cowrie_events"] = len(filtered)
execution_log["end_time"] = str(datetime.now())

# =====================================================
# Save Controller Log
# =====================================================

os.makedirs("execution_logs", exist_ok=True)
stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

base = (
    scenario["scenario"]
    .replace(" ", "_")
    .replace("/", "_")
)

controller_log = os.path.join(
    "execution_logs",
    f"{base}_{stamp}.json"
)

with open(controller_log, "w") as f:
    json.dump(execution_log, f, indent=4)

print(f"[+] Controller Log Saved : {controller_log}")

# =====================================================
# Save Filtered Cowrie Log
# =====================================================

if session is not None:

    cowrie_log = os.path.join(
        "execution_logs",
        f"{base}_{stamp}_cowrie.json"
    )

    with open(cowrie_log, "w") as f:
        json.dump(filtered, f, indent=4)

    print(f"[+] Cowrie Log Saved : {cowrie_log}")

else:

    print("[!] No Cowrie log generated because no session was detected.")

print("Done.")
