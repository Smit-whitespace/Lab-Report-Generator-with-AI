from openai import OpenAI
from app.core.config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


def fallback_summary(template_name: str, results: dict) -> str:
    summary = f"Test: {template_name}\n"

    for key, value in results.items():
        summary += f"- {key}: {value}\n"

    summary += "\nNote: Automated summary (AI unavailable)."
    return summary


def standard_summary(template_name: str, results: dict) -> str:
    summary = f"Test: {template_name}\n"

    for key, value in results.items():
        summary += f"- {key}: {value}\n"

    summary += "\nNote: AI-generated description is disabled."
    return summary


def generate_summary(template_name: str, results: dict) -> str:
    try:
        prompt = f"""
You are a medical lab assistant.

Test Name: {template_name}

Results:
{results}

Write a concise, professional medical summary with observations.
Avoid diagnosis. Keep it clear and readable.
"""

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        return response.choices[0].message.content

    except Exception as e:
        print("AI failed:", e)
        return fallback_summary(template_name, results)
