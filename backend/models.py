from sqlalchemy import Column, Integer, String, DateTime
from database import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    msg_date = Column(DateTime)      # وقت الإصدار
    msg_arrival = Column(DateTime)   # وقت الوصول
    msg_type = Column(String)        
    filename = Column(String)        # اسم الملف للتحقق من COR
    classification = Column(String)  