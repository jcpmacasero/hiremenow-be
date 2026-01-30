from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.conversation import (
    Conversation,
    ConversationParticipant,
    Message,
    MessageRead,
    ConversationType,
    MessageContentType,
)
from app.schemas.conversation import (
    ConversationResponse,
    ConversationListResponse,
    ConversationCreate,
    MessageResponse,
    MessageCreate,
)

router = APIRouter(prefix="/conversations", tags=["conversations"])


def _user_in_conversation(db: Session, conversation_id: UUID, user_id: UUID) -> bool:
    return (
        db.query(ConversationParticipant)
        .filter(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == user_id,
        )
        .first()
        is not None
    )


@router.get("", response_model=ConversationListResponse)
def list_conversations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List conversations the current user participates in."""
    subq = (
        db.query(ConversationParticipant.conversation_id)
        .filter(ConversationParticipant.user_id == current_user.id)
    )
    query = db.query(Conversation).filter(Conversation.id.in_(subq)).order_by(Conversation.updated_at.desc())
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return ConversationListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    data: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a direct conversation with one or more participants."""
    conv = Conversation(type=data.type or "direct", subject=data.subject)
    db.add(conv)
    db.flush()
    part = ConversationParticipant(conversation_id=conv.id, user_id=current_user.id, role="member")
    db.add(part)
    for uid in data.participant_user_ids or []:
        if uid != current_user.id:
            db.add(ConversationParticipant(conversation_id=conv.id, user_id=uid, role="member"))
    db.commit()
    db.refresh(conv)
    return conv


@router.get("/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a conversation by ID (must be participant)."""
    if not _user_in_conversation(db, conversation_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conv


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
def list_messages(
    conversation_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List messages in a conversation."""
    if not _user_in_conversation(db, conversation_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    items = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items


@router.post("/{conversation_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def send_message(
    conversation_id: UUID,
    data: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send a message in a conversation."""
    if not _user_in_conversation(db, conversation_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    msg = Message(
        conversation_id=conversation_id,
        sender_id=current_user.id,
        content=data.content,
        content_type=data.content_type or MessageContentType.TEXT,
    )
    db.add(msg)
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conv:
        conv.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(msg)
    return msg


@router.put("/{conversation_id}/read", status_code=status.HTTP_204_NO_CONTENT)
def mark_conversation_read(
    conversation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark all messages in conversation as read for current user."""
    if not _user_in_conversation(db, conversation_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    part = (
        db.query(ConversationParticipant)
        .filter(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == current_user.id,
        )
        .first()
    )
    if part:
        part.last_read_at = datetime.utcnow()
        db.commit()
    return None
