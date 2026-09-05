from sqlalchemy import create_engine, Column, String, Float, \
                       Integer, Text, DateTime, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone

import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aria.db")

if DATABASE_URL.startswith("postgresql"):
    engine = create_engine(
        DATABASE_URL,
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True
    )
else:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False, "timeout": 30} if "sqlite" in DATABASE_URL else {}
    )

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

def get_utc_now():
    return datetime.now(timezone.utc)

class Payment(Base):
    __tablename__ = "payments"
    payment_id        = Column(String, primary_key=True)
    amount            = Column(Float, default=1000.0)
    payment_method    = Column(String, default="upi")
    bank              = Column(String, default="HDFC")
    customer_id       = Column(String, default="cust_unknown")
    past_failure_rate = Column(Float, default=0.2)
    time_of_day       = Column(Integer, default=14)
    pincode_tier      = Column(Integer, default=2)
    failure_reason    = Column(String, default="bank_timeout")
    risk_score        = Column(Float, nullable=True)
    root_cause        = Column(String, nullable=True)
    status            = Column(String, default="pending")
    created_at        = Column(DateTime, default=get_utc_now)

class Action(Base):
    __tablename__ = "actions"
    action_id              = Column(Integer, primary_key=True, autoincrement=True)
    payment_id             = Column(String, index=True)
    attempt_number         = Column(Integer, default=1)
    strategy_chosen        = Column(String)
    strategy_weight        = Column(Float)
    reasoning_trace        = Column(Text)
    outcome                = Column(String)
    audio_url              = Column(String, nullable=True)
    executed_at            = Column(DateTime, default=get_utc_now)

class StrategyWeight(Base):
    __tablename__ = "strategy_weights"
    id               = Column(Integer, primary_key=True, autoincrement=True)
    payment_number   = Column(Integer)
    failure_class    = Column(String)
    retry_weight     = Column(Float)
    emi_weight       = Column(Float)
    voice_weight     = Column(Float)
    whatsapp_weight  = Column(Float)
    escalate_weight  = Column(Float)
    recorded_at      = Column(DateTime, default=get_utc_now)

class Exception_(Base):
    __tablename__ = "exceptions"
    id             = Column(Integer, primary_key=True, autoincrement=True)
    payment_id     = Column(String, index=True)
    reason         = Column(String)
    attempts_made  = Column(Integer)
    postmortem     = Column(Text)
    escalated_at   = Column(DateTime, default=get_utc_now)

def init_db():
    Base.metadata.create_all(bind=engine)
    if "sqlite" in DATABASE_URL:
        try:
            with engine.connect() as conn:
                conn.execute(text("PRAGMA journal_mode=WAL;"))
        except Exception:
            pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

