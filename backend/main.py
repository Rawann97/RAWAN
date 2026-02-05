from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import time
from database import SessionLocal, engine, Base
from models import Message
from pydantic import BaseModel

# Create tables
while True:
    try:
        Base.metadata.create_all(bind=engine)
        break
    except:
        time.sleep(2)

app = FastAPI()

class MessageCreate(BaseModel):
    msg_date: datetime
    msg_arrival: datetime
    msg_type: str
    filename: str

def classify_opmet(msg_date, msg_arrival, msg_type, filename):
    diff = (msg_arrival - msg_date).total_seconds() / 60
    
    if "COR" in filename.upper():
        return "COR" if diff <= 45 else "CORR"
    
    if any(msg_type.startswith(c) for c in ["TT", "UU", "UP", "UG"]):
        return "1" if msg_arrival else "0"

    if msg_type.startswith("SA"):
        return "" if diff <= 14 else ("R" if diff <= 45 else "N")

    return "" if diff <= 0 else ("R" if diff <= 9 else "N")

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

@app.post("/messages")
def create_message(msg: MessageCreate, db: Session = Depends(get_db)):
    res = classify_opmet(msg.msg_date, msg.msg_arrival, msg.msg_type, msg.filename)
    db_msg = Message(**msg.dict(), classification=res)
    db.add(db_msg)
    db.commit()
    return {"status": "success", "result": res}

@app.get("/messages")
def get_messages(db: Session = Depends(get_db)):
    return db.query(Message).all()