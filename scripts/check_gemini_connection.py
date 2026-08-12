from src.llm.gemini_client import GeminiClient


client = GeminiClient()

response = client.generate(
    "Explain in one sentence what a credit assessment is."
)

print(response)