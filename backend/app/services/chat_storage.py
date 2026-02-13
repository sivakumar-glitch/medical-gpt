import json
import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from app.models.conversation import Conversation, ConversationList, Message
import threading

class ChatStorageService:
    def __init__(self, base_path: str = "data/chat_history"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
    
    def _get_user_dir(self, user_id: int) -> Path:
        """Get or create user's chat history directory"""
        user_dir = self.base_path / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir
    
    def _get_conversation_path(self, user_id: int, conversation_id: str) -> Path:
        """Get path to conversation file"""
        return self._get_user_dir(user_id) / f"{conversation_id}.json"
    
    def save_conversation(self, conversation: Conversation) -> Conversation:
        """Save or update a conversation"""
        with self.lock:
            conversation.updated_at = datetime.utcnow()
            file_path = self._get_conversation_path(conversation.user_id, conversation.id)
            
            # Convert to dict for JSON serialization
            data = conversation.model_dump(mode='json')
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            return conversation
    
    def load_conversation(self, user_id: int, conversation_id: str) -> Optional[Conversation]:
        """Load a specific conversation"""
        file_path = self._get_conversation_path(user_id, conversation_id)
        
        if not file_path.exists():
            return None
        
        with self.lock:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return Conversation(**data)
    
    def list_conversations(self, user_id: int) -> List[ConversationList]:
        """List all conversations for a user"""
        user_dir = self._get_user_dir(user_id)
        conversations = []
        
        for file_path in user_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                conversations.append(ConversationList(
                    id=data['id'],
                    title=data['title'],
                    created_at=data['created_at'],
                    updated_at=data['updated_at'],
                    message_count=len(data.get('messages', []))
                ))
            except Exception as e:
                print(f"Error loading conversation {file_path}: {e}")
                continue
        
        # Sort by updated_at descending (most recent first)
        conversations.sort(key=lambda x: x.updated_at, reverse=True)
        return conversations
    
    def delete_conversation(self, user_id: int, conversation_id: str) -> bool:
        """Delete a conversation"""
        file_path = self._get_conversation_path(user_id, conversation_id)
        
        if not file_path.exists():
            return False
        
        with self.lock:
            file_path.unlink()
            return True
    
    def add_message(self, user_id: int, conversation_id: str, message: Message) -> Optional[Conversation]:
        """Add a message to an existing conversation"""
        conversation = self.load_conversation(user_id, conversation_id)
        
        if not conversation:
            return None
        
        conversation.messages.append(message)
        return self.save_conversation(conversation)

# Global instance
chat_storage = ChatStorageService()
