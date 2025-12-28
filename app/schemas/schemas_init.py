from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class Message(BaseModel):
    """Схема сообщения"""
    role: str = Field(..., description="Роль отправителя: user или assistant")
    content: str = Field(..., description="Содержание сообщения")
    timestamp: datetime = Field(default_factory=datetime.now)


class ChatHistory(BaseModel):
    """История чата"""
    user_id: int
    messages: List[Message] = Field(default_factory=list)
    
    def add_message(self, role: str, content: str):
        self.messages.append(Message(role=role, content=content))
    
    def get_context(self, max_messages: int = 10) -> List[Dict[str, str]]:
        """Получить последние N сообщений для контекста"""
        recent = self.messages[-max_messages:] if len(self.messages) > max_messages else self.messages
        return [{"role": msg.role, "content": msg.content} for msg in recent]


class Document(BaseModel):
    """Схема документа для RAG"""
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None


class RAGResponse(BaseModel):
    """Ответ от RAG pipeline"""
    answer: str
    sources: List[str] = Field(default_factory=list)
    confidence: float = 0.0
