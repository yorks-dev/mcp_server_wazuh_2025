from openai import OpenAI
from app.config import settings

# Initialize client
client = OpenAI(api_key=settings.OPENAI_API_KEY)

def ask_openai(prompt: str):
    """Send user prompt to OpenAI LLM."""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an intelligent MCP server assistant."},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[ERROR] OpenAI request failed: {e}")
        return "LLM request failed."
    

    
