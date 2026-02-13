from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List
from app.auth.deps import get_current_user
from app.models.user import User
from app.rag.rag_service import rag_service
from app.services.llm_service import llm_service
from app.safety.guardrails import safety_service
from langsmith import traceable

router = APIRouter()

class ChatRequest(BaseModel):
    query: str
    conversation_id: str | None = None  # Optional conversation ID
    history: List[dict] = [] # [{"role": "user", "content": "..."}, ...]

@router.post("/chat")
@traceable(name="Chat Endpoint")
async def chat_stream(
    request: ChatRequest,
    # current_user: User = Depends(get_current_user) # Temporarily optional for demo
):
    user_message = request.query
    
    # 1. Safety Checks
    # a. Emergency
    emergency_msg = safety_service.check_emergency(user_message)
    if emergency_msg:
        # Return immediate emergency response (not streaming to be safe and clear)
        # However, frontend expects stream. We can stream this static message.
        def emergency_stream():
            yield emergency_msg
        return StreamingResponse(emergency_stream(), media_type="text/event-stream")
    
    # b. Injection / Toxicity
    is_safe, reason = safety_service.is_safe_input(user_message)
    if not is_safe:
        def safety_stream():
            yield f"I cannot process your request. {reason}"
        return StreamingResponse(safety_stream(), media_type="text/event-stream")
    
    # 2. RAG Retrieval
    retrieved_docs = rag_service.retrieve(user_message, k=3)
    context_str = rag_service.format_context(retrieved_docs)
    
    # 3. Construct Prompt
    system_prompt = (
        "You are a helpful and safe medical assistant. "
        "Use the following retrieved context to answer the user's question. "
        "If the answer is not in the context, say you don't know but don't hallucinate. "
        "Always provide a helpful, empathetic tone.\n\n"

        "RESPONSE GUIDELINES:\n"
        "- Keep responses concise and to the point (2-4 sentences max)\n"
        "- Use simple, everyday language - avoid medical jargon unless necessary\n"
        "- Explain any medical terms in plain English\n"
        "- Be direct and clear\n\n"
        "FORMATTING RULES:\n"
        "1. Use numbered lists (1., 2., 3.) or bullet points (-) for multiple points\n"
        "2. Each point should be on a NEW LINE\n"
        "3. Use **bold** ONLY for key medical terms (1-2 words max)\n"
        "4. Keep supporting text in regular font\n"
        "5. Use short, clear sentences\n\n"
        f"Context:\n{context_str}"
    )
    
    # 4. Stream Response in SSE format
    async def sse_wrapper():
        async for chunk in llm_service.get_response_stream(user_message, system_role=system_prompt):
            if chunk:
                # SSE format: data: <content>\n\n
                yield f"data: {chunk}\n\n"

    return StreamingResponse(
        sse_wrapper(),
        media_type="text/event-stream"
    )
