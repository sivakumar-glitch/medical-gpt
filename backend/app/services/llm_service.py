import os
import openai
from app.core.config import settings
from typing import AsyncGenerator
from langsmith import traceable

class LLMService:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        if self.api_key:
            openai.api_key = self.api_key
        
    @traceable(name="LLM Generation Stream")
    async def get_response_stream(self, prompt: str, system_role: str = "system") -> AsyncGenerator[str, None]:
        if (not self.api_key or self.api_key == "CHANGE_THIS_TO_A_SECURE_SECRET_KEY_IN_ENV") and not settings.AZURE_OPENAI_API_KEY:
            # Mock response if no key
            yield "No OpenAI API key found. Running in MOCK mode.\n\n"
            yield "Here is a simulated response based on your query:\n"
            yield f"'{prompt}' is an interesting medical question.\n"
            yield "This system is designed to provide medical information based on retrieving documents from the knowledge base.\n"
            yield "Please configure the OpenAI API Key to get real AI responses."
            return

        try:
            # Check if Azure config is present
            if settings.AZURE_OPENAI_ENDPOINT:
                from openai import AsyncAzureOpenAI
                client = AsyncAzureOpenAI(
                    api_key=settings.AZURE_OPENAI_API_KEY,
                    api_version=settings.AZURE_OPENAI_API_VERSION,
                    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
                )
                model_name = settings.AZURE_OPENAI_DEPLOYMENT
            else:
                from openai import AsyncOpenAI
                client = AsyncOpenAI(api_key=self.api_key)
                model_name = "gpt-3.5-turbo"
            
            stream = await client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_role},
                    {"role": "user", "content": prompt}
                ],
                stream=True,
            )
            
            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta and delta.content:
                        yield delta.content
                    
        except Exception as e:
            error_str = str(e)
            # Handle content filter violations gracefully
            if "content_filter" in error_str or "ResponsibleAIPolicyViolation" in error_str:
                yield "I understand your medical question. However, I'm unable to process this specific request due to content policy restrictions. "
                yield "Please try rephrasing your question in a different way, such as: \n"
                yield "- 'How do doctors treat [condition]?' \n"
                yield "- 'What are the treatment options for [condition]?' \n"
                yield "- 'How can I manage [condition]?' \n\n"
                yield "If you continue to have issues, please rephrase your medical question or contact support."
            elif "insufficient_quota" in error_str or "429" in error_str:
                yield "\n\n⚠️ **LLM Quota Exceeded**: Falling back to MOCK mode for demonstration.\n\n"
                yield "The RAG pipeline successfully retrieved context, but your OpenAI account has no credits.\n"
                yield f"System Prompt Context would have included medical documents relevant to your query.\n\n"
                yield "Please check your OpenAI billing or provide a different API key in `.env`."
            else:
                yield f"Sorry, I encountered a technical issue while processing your request. Please try again."

llm_service = LLMService()
