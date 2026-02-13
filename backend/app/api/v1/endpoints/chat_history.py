from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.auth.deps import get_current_user
from app.models.user import User
from app.models.conversation import (
    Conversation, 
    ConversationCreate, 
    ConversationUpdate, 
    ConversationList,
    Message
)
from app.services.chat_storage import chat_storage
from datetime import datetime

router = APIRouter()

@router.get("/conversations", response_model=List[ConversationList])
async def list_conversations(
    current_user: User = Depends(get_current_user)
):
    """List all conversations for the current user"""
    return chat_storage.list_conversations(current_user.id)

@router.get("/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific conversation"""
    conversation = chat_storage.load_conversation(current_user.id, conversation_id)
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return conversation

@router.post("/conversations", response_model=Conversation, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new conversation"""
    conversation = Conversation(
        user_id=current_user.id,
        title=conversation_data.title,
        messages=conversation_data.messages
    )
    
    return chat_storage.save_conversation(conversation)

@router.put("/conversations/{conversation_id}", response_model=Conversation)
async def update_conversation(
    conversation_id: str,
    update_data: ConversationUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a conversation (rename or add messages)"""
    conversation = chat_storage.load_conversation(current_user.id, conversation_id)
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Update fields if provided
    if update_data.title is not None:
        conversation.title = update_data.title
    
    if update_data.messages is not None:
        conversation.messages = update_data.messages
    
    return chat_storage.save_conversation(conversation)

@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a conversation"""
    success = chat_storage.delete_conversation(current_user.id, conversation_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return None

@router.post("/conversations/{conversation_id}/messages", response_model=Conversation)
async def add_message(
    conversation_id: str,
    message: Message,
    current_user: User = Depends(get_current_user)
):
    """Add a message to a conversation"""
    conversation = chat_storage.add_message(current_user.id, conversation_id, message)
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return conversation
