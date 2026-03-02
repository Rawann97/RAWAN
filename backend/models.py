from sqlalchemy import Column, Integer, String, DateTime, Boolean
from database import Base
from datetime import datetime

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    msg_date = Column(DateTime)      # وقت الإصدار
    msg_arrival = Column(DateTime)   # وقت الوصول
    msg_type = Column(String)        
    filename = Column(String)        # اسم الملف للتحقق من COR
    classification = Column(String)  
    created_at = Column(DateTime, default=datetime.utcnow)

    is_approved = Column(Boolean, default=False)
    approved_by = Column(String, nullable=True) # اسم المشرف
    approved_at = Column(DateTime, nullable=True) # وقت الموافقة