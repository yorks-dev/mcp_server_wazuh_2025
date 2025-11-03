from openai import OpenAI
from app.config import settings  # or wherever your .env is loaded

# Create the OpenAI client
client = OpenAI(api_key=settings.OPENAI_API_KEY)

def ask_openai(prompt: str):
    """Send a query to the OpenAI model."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # or "gpt-4o" depending on your key access
        messages=[
            {"role": "system", "content": "You are an MCP assistant connected to Wazuh SIEM."},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content
