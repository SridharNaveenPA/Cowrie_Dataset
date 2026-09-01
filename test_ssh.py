import json

from llm import ask_llm


scenario = {
    "scenario": "Credential Discovery",
    "description": (
        "Discover credentials, secrets, SSH keys, "
        "API tokens and authentication artifacts."
    )
}


history = [
    {
        "command": "whoami",
        "output": "root",
        "goal": "User Identification"
    }
]


result = ask_llm(
    scenario,
    history
)


print("\nLLM RESPONSE:")
print(json.dumps(result, indent=4))