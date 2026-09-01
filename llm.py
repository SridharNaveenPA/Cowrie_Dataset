import json
import requests


OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODEL = "qwen3:1.7b"


SYSTEM_PROMPT = """
You are an autonomous attacker operating ONLY inside an isolated Linux
honeypot environment.

Your task is to perform the specified security-testing scenario.

You receive:
- the scenario objective
- previous commands
- their outputs
- the current state of the session

Your job is to select ONE useful next command.

IMPORTANT RULES:

1. Return ONLY valid JSON.
2. Do not return Markdown.
3. Do not return explanations outside JSON.
4. Select exactly ONE command.
5. The command must be intended to run inside the Cowrie honeypot.
6. Do not execute commands yourself.
7. Do not invent command output.
8. Use previous command output to decide what to investigate next.
9. Avoid repeating commands unless there is a good reason.
10. Stop when the objective has been sufficiently investigated.

Return exactly this structure:

{
    "action": "execute",
    "command": "command_here",
    "reason": "short explanation",
    "goal": "current sub-goal"
}

When the scenario objective has been sufficiently completed, return:

{
    "action": "stop",
    "command": "",
    "reason": "objective completed",
    "goal": "completed"
}
"""


def ask_llm(
    scenario,
    history,
    max_output_chars=12000
):
    """
    Send the current attacker state to Ollama
    and receive the next action as JSON.
    """

    context = {
        "scenario": {
            "name": scenario.get("scenario"),
            "description": scenario.get("description")
        },
        "history": history[-10:]
    }

    user_prompt = f"""
SCENARIO:

{json.dumps(context, indent=2)}

Choose the next action.

Remember:
- Return ONLY JSON.
- Choose ONE command.
- Use the command results in the history.
"""

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.2,
            "num_predict": 300
        }
    }

    try:

        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=120
        )

        response.raise_for_status()

        data = response.json()

        content = data["message"]["content"]

        result = json.loads(content)

        if not isinstance(result, dict):
            raise ValueError("LLM response is not a JSON object")

        return result

    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Cannot connect to Ollama at "
            "http://127.0.0.1:11434"
        )

    except requests.exceptions.Timeout:
        raise RuntimeError(
            "Ollama request timed out"
        )

    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"LLM returned invalid JSON: {e}"
        )

    except Exception as e:
        raise RuntimeError(
            f"LLM error: {e}"
        )