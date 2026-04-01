from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from core.database import Base
from datetime import datetime

class ActionHistory(Base):
    __tablename__ = "action_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    action_type = Column(String(50), nullable=False)
    payload = Column(JSONB, nullable=False)  # PostgreSQL의 JSONB 사용으로 오브젝트 원형 보존
    is_undone = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
