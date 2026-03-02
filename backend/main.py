import os
import time
import pandas as pd
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import SessionLocal, engine
import models
from datetime import datetime

def get_full_message_type(msg_code):
    mapping = {
        "SA": "METAR", "FT": "TAF", "SM": "SAYNOP", "SI": "SAYNOP",
        "US": "TTAA", "UK": "TTBB", "UL": "TTCC", "UE": "TTDD",
        "FQ": "MARINE", "FZ": "MAFOR", "SP": "SPECI", "SX": "Highest Temperature Recorded",
        "UG": "PAILOT", "UH": "PAILOT", "UP": "PAILOT", "UQ": "PAILOT",
        "WS": "SIGMET Warning", "WW": "Aerodrome Warning", "LA": "METAR",
        "LS": "SIGMET Warning", "LT": "TAF Forecast"
    }
    short_code = str(msg_code)[:2].upper()
    return mapping.get(short_code, msg_code)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

def classify_message(row, filename):
    raw_type = str(row.get('msg_type', '')).strip()
    m_full_type = get_full_message_type(raw_type)
    if pd.isna(row.get('msg_arrival')): return "0"
    if pd.isna(row.get('msg_date')): return "Missing Data"
    
    sch = pd.to_datetime(row['msg_date'])
    act = pd.to_datetime(row['msg_arrival'])
    delay = (act - sch).total_seconds() / 60
    
    if "COR" in str(filename).upper() or "COR" in raw_type.upper():
        return "COR" if delay <= 45 else "CORR"
    if m_full_type == "METAR":
        return "Valid (METAR)" if delay <= 14 else ("R" if delay <= 45 else "N")
    if "TAF" in m_full_type:
        return "Valid (TAF)" if delay <= 0 else ("R" if delay <= 9 else "N")
    
    list_ones = ["PAILOT", "SIGMET Warning", "SAYNOP", "TTAA", "TTBB", "TTCC", "TTDD", "MARINE", "MAFOR", "Highest Temperature Recorded", "Aerodrome Warning"]
    if m_full_type in list_ones: return "1"
    
    return "Valid" if delay <= 0 else ("R" if delay <= 9 else "N")

@app.on_event("startup")
async def load_data():
    time.sleep(5)  
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        db.query(models.Message).delete()
        db.commit()
        path = "/app/Data"
        if os.path.exists(path):
            for file in os.listdir(path):
                if file.endswith((".xlsx", ".xls")):
                    df = pd.read_excel(os.path.join(path, file))
                    for _, row in df.iterrows():
                        full_type = get_full_message_type(row.get('msg_type', 'SA'))
                        db.add(models.Message(
                            msg_date=pd.to_datetime(row['msg_date']),
                            msg_arrival=pd.to_datetime(row['msg_arrival']),
                            msg_type=full_type,
                            filename=file,
                            classification=classify_message(row, file)
                        ))
            db.commit()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

@app.get("/messages")
def get_messages(db: Session = Depends(get_db)):
    return db.query(models.Message).all()


@app.get("/stats/summary")
def get_summary_stats(db: Session = Depends(get_db)):
    total = db.query(models.Message).count()
    valid = db.query(models.Message).filter(models.Message.classification.like('%Valid%')).count()
    missing = db.query(models.Message).filter(models.Message.classification == "0").count()
    
    completion_rate = (valid / total * 100) if total > 0 else 0
    missing_rate = (missing / total * 100) if total > 0 else 0
    
    return {
        "total": total,
        "completion_rate": round(completion_rate, 2),
        "missing_rate": round(missing_rate, 2)
    }


@app.post("/messages/{msg_id}/approve")
def approve_message(msg_id: int, name: str, db: Session = Depends(get_db)):
    msg = db.query(models.Message).filter(models.Message.id == msg_id).first()
    if msg:
        msg.is_approved = True
        msg.approved_by = name 
        msg.approved_at = datetime.utcnow()
        db.commit()
        return {"status": "Success"}
    return {"error": "Not found"}