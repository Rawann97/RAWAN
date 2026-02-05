from fastapi import FastAPI
import pandas as pd
from sqlalchemy import create_engine

app = FastAPI()


DATABASE_URL = "postgresql://postgres@db:5432/postgres"

@app.get("/")
def home():
    return {"message": "Welcome to Rawan's System Components"}

@app.get("/summary")
def get_summary():
    try:
        engine = create_engine(DATABASE_URL)
        query = "SELECT class, count(*) as total FROM classified_messages GROUP BY class"
        df = pd.read_sql(query, engine)
        return df.set_index('class')['total'].to_dict()
    except Exception as e:
        return {"error": str(e)}