import json

from groq import Groq
from pydantic import ValidationError

from app.config import GROQ_API_KEY, LLM_MAX_RETRIES, LLM_MODEL


class LLMError(Exception):
    pass


client = None


def get_client():
    global client
    if client is None:
        if not GROQ_API_KEY:
            raise LLMError("GROQ_API_KEY set nahi hai. .env file check karo.")
        client = Groq(api_key=GROQ_API_KEY)
    return client


def generate_structured(system, user, schema):
    schema_json = json.dumps(schema.model_json_schema())

    messages = [
        {
            "role": "system",
            "content": system + "\n\nReturn ONLY a valid JSON object matching this schema:\n" + schema_json,
        },
        {"role": "user", "content": user},
    ]

    error = ""
    for attempt in range(LLM_MAX_RETRIES + 1):
        resp = get_client().chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=0,
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content or ""

        try:
            data = json.loads(content)
            return schema.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as e:
            error = str(e)
            messages.append({"role": "assistant", "content": content})
            messages.append(
                {
                    "role": "user",
                    "content": "Your JSON was invalid: " + error[:800] + "\nFix it and return only the corrected JSON.",
                }
            )

    raise LLMError("LLM valid output nahi de paya: " + error[:300])