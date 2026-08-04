import json
import os
import time
from datetime import datetime
import paramiko

# =====================================================
# Cowrie SSH Configuration
# =====================================================

HOST = "127.0.0.1"
PORT = 2222
USERNAME = "root"
PASSWORD = "password"

# =====================================================
# Available Attack Scenarios
# =====================================================

SCENARIOS = {
    "1": {
        "name": "Credential Discovery",
        "file": "credential_discovery.json",
        "description": (
            "Searches for credentials, SSH keys, API tokens, configuration files,\n"
            "and sensitive information available on the compromised system."
        ),
    },

    "2": {
        "name": "Privilege Escalation",
        "file": "privilege_escalation.json",
        "description": (
            "Performs system enumeration to identify potential privilege\n"
            "escalation opportunities such as SUID binaries and sudo access."
        ),
    },

    "3": {
        "name": "Persistence",
        "file": "persistence.json",
        "description": (
            "Explores persistence mechanisms including cron jobs, startup\n"
            "scripts, SSH configurations and scheduled services."
        ),
    },

    "4": {
        "name": "Lateral Movement",
        "file": "lateral_movement.json",
        "description": (
            "Discovers neighboring hosts, SSH configurations and network\n"
            "information useful for moving across an enterprise network."
        ),
    },

    "5": {
        "name": "Ransomware Behaviour",
        "file": "ransomware.json",
        "description": (
            "Simulates reconnaissance performed by ransomware operators before\n"
            "encrypting files by locating valuable data and storage devices."
        ),
    }
}


# =====================================================
# Display Menu
# =====================================================

print("\n")
print("=" * 70)
print("         COWRIE HONEYPOT ATTACK SCENARIO SIMULATOR")
print("=" * 70)

for key, value in SCENARIOS.items():

    print(f"\n[{key}] {value['name']}")
    print(value["description"])

print("\n" + "=" * 70)

choice = input("Select a scenario (1-5): ").strip()

if choice not in SCENARIOS:
    print("\nInvalid selection.")
    exit()

selected = SCENARIOS[choice]

json_file = os.path.join("JSONs", selected["file"])

print(f"\nSelected Scenario : {selected['name']}")
print("Loading scenario...\n")

# =====================================================
# Load JSON
# =====================================================

with open(json_file, "r") as file:
    scenario = json.load(file)

# =====================================================
# Connect to Cowrie
# =====================================================

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

print("[*] Connecting to Cowrie...")

client.connect(
    HOST,
    port=PORT,
    username=USERNAME,
    password=PASSWORD,
    allow_agent=False,
    look_for_keys=False
)

print("[+] Connected Successfully.\n")

shell = client.invoke_shell()

time.sleep(2)

if shell.recv_ready():
    shell.recv(65535)

# =====================================================
# Logging
# =====================================================

execution_log = {
    "scenario": scenario["scenario"],
    "start_time": str(datetime.now()),
    "phases": []
}

# =====================================================
# Execute Commands
# =====================================================

for phase in scenario["phases"]:

    print("=" * 70)
    print(f"PHASE : {phase['phase']}")
    print("=" * 70)

    phase_log = {
        "phase": phase["phase"],
        "commands": []
    }

    for command_info in phase["commands"]:

        command = command_info["command"]

        print(f"\n>>> {command}")

        shell.send(command + "\n")

        time.sleep(2)

        output = ""

        while shell.recv_ready():
            output += shell.recv(65535).decode(errors="ignore")

        print(output)

        phase_log["commands"].append({

            "id": command_info.get("id", ""),

            "command": command,

            "purpose": command_info.get("purpose", ""),

            "severity": command_info.get("severity", ""),

            "expected_outcome": command_info.get("expected_outcome", ""),

            "timestamp": str(datetime.now()),

            "output": output

        })

    execution_log["phases"].append(phase_log)

# =====================================================
# Close SSH
# =====================================================

shell.send("exit\n")

time.sleep(1)

client.close()

execution_log["end_time"] = str(datetime.now())

# =====================================================
# Save Log
# =====================================================

os.makedirs("execution_logs", exist_ok=True)

filename = (
    scenario["scenario"]
    .replace(" ", "_")
    .replace("/", "_")
)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

outfile = os.path.join(
    "execution_logs",
    f"{filename}_{timestamp}.json"
)

with open(outfile, "w") as file:
    json.dump(execution_log, file, indent=4)

print("\n")
print("=" * 70)
print("Scenario Execution Complete")
print(f"Execution Log Saved : {outfile}")
print("=" * 70)