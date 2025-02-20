from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, Float, DateTime, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uvicorn

app = FastAPI()

# Database setup - using a server-specific database name
SQLALCHEMY_DATABASE_URL = "sqlite:///./server_typing_scores.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

Base = declarative_base()

class ServerScore(Base):
    __tablename__ = "server_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String, default="Anonymous")
    
    # Round scores
    round1_score = Column(Float)
    round2_score = Column(Float)
    round3_score = Column(Float)
    
    # Detailed metrics for each round
    round1_wpm = Column(Float)
    round1_accuracy = Column(Float)
    round1_gross_wpm = Column(Float)
    round1_error_rate = Column(Float)
    
    round2_wpm = Column(Float)
    round2_accuracy = Column(Float)
    round2_gross_wpm = Column(Float)
    round2_error_rate = Column(Float)
    
    round3_wpm = Column(Float)
    round3_accuracy = Column(Float)
    round3_gross_wpm = Column(Float)
    round3_error_rate = Column(Float)
    
    # Overall metrics
    average_score = Column(Float)
    average_wpm = Column(Float)
    average_accuracy = Column(Float)
    average_error_rate = Column(Float)
    
    timestamp = Column(DateTime, default=datetime.utcnow)
    test_duration = Column(Integer)  # in seconds
    ip_address = Column(String)

Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Pydantic models for request validation
class RoundMetrics(BaseModel):
    wpm: float
    accuracy: float
    gross_wpm: float
    error_rate: float
    final_score: float

class ScoreSubmission(BaseModel):
    user_name: str = "Anonymous"
    round1: RoundMetrics
    round2: RoundMetrics
    round3: RoundMetrics
    test_duration: int = 60

@app.post("/submit-scores")
async def submit_scores(scores: ScoreSubmission, ip_address: str = None):
    try:
        db = SessionLocal()
        
        # Calculate average metrics
        average_score = (scores.round1.final_score + scores.round2.final_score + scores.round3.final_score) / 3
        average_wpm = (scores.round1.wpm + scores.round2.wpm + scores.round3.wpm) / 3
        average_accuracy = (scores.round1.accuracy + scores.round2.accuracy + scores.round3.accuracy) / 3
        average_error_rate = (scores.round1.error_rate + scores.round2.error_rate + scores.round3.error_rate) / 3
        
        db_score = ServerScore(
            user_name=scores.user_name,
            
            # Round scores
            round1_score=scores.round1.final_score,
            round2_score=scores.round2.final_score,
            round3_score=scores.round3.final_score,
            
            # Round 1 metrics
            round1_wpm=scores.round1.wpm,
            round1_accuracy=scores.round1.accuracy,
            round1_gross_wpm=scores.round1.gross_wpm,
            round1_error_rate=scores.round1.error_rate,
            
            # Round 2 metrics
            round2_wpm=scores.round2.wpm,
            round2_accuracy=scores.round2.accuracy,
            round2_gross_wpm=scores.round2.gross_wpm,
            round2_error_rate=scores.round2.error_rate,
            
            # Round 3 metrics
            round3_wpm=scores.round3.wpm,
            round3_accuracy=scores.round3.accuracy,
            round3_gross_wpm=scores.round3.gross_wpm,
            round3_error_rate=scores.round3.error_rate,
            
            # Overall metrics
            average_score=average_score,
            average_wpm=average_wpm,
            average_accuracy=average_accuracy,
            average_error_rate=average_error_rate,
            
            test_duration=scores.test_duration,
            ip_address=ip_address
        )
        db.add(db_score)
        db.commit()
        return {
            "message": "Scores submitted successfully",
            "average_score": average_score,
            "average_wpm": average_wpm,
            "average_accuracy": average_accuracy
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/scores")
async def get_scores():
    try:
        db = SessionLocal()
        scores = db.query(ServerScore).all()
        return [
            {
                "id": score.id,
                "user_name": score.user_name,
                "round1_score": score.round1_score,
                "round2_score": score.round2_score,
                "round3_score": score.round3_score,
                "average_score": score.average_score,
                "average_wpm": score.average_wpm,
                "average_accuracy": score.average_accuracy,
                "timestamp": score.timestamp
            }
            for score in scores
        ]
    finally:
        db.close()

@app.get("/user-scores/{user_name}")
async def get_user_scores(user_name: str):
    try:
        db = SessionLocal()
        scores = db.query(ServerScore).filter(ServerScore.user_name == user_name).all()
        return [
            {
                "id": score.id,
                "timestamp": score.timestamp,
                "rounds": {
                    "round1": {
                        "score": score.round1_score,
                        "wpm": score.round1_wpm,
                        "accuracy": score.round1_accuracy,
                        "error_rate": score.round1_error_rate
                    },
                    "round2": {
                        "score": score.round2_score,
                        "wpm": score.round2_wpm,
                        "accuracy": score.round2_accuracy,
                        "error_rate": score.round2_error_rate
                    },
                    "round3": {
                        "score": score.round3_score,
                        "wpm": score.round3_wpm,
                        "accuracy": score.round3_accuracy,
                        "error_rate": score.round3_error_rate
                    }
                },
                "averages": {
                    "score": score.average_score,
                    "wpm": score.average_wpm,
                    "accuracy": score.average_accuracy,
                    "error_rate": score.average_error_rate
                }
            }
            for score in scores
        ]
    finally:
        db.close()

@app.get("/leaderboard")
async def get_leaderboard():
    try:
        db = SessionLocal()
        top_scores = db.query(ServerScore).order_by(ServerScore.average_score.desc()).limit(10).all()
        return [
            {
                "user_name": score.user_name,
                "average_score": score.average_score,
                "average_wpm": score.average_wpm,
                "average_accuracy": score.average_accuracy,
                "timestamp": score.timestamp
            }
            for score in top_scores
        ]
    finally:
        db.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 