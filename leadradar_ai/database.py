import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from .config import settings

engine = create_engine(
    settings.DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    company_name = Column(String(255), default="My SaaS")
    product_name = Column(String(255), default="My Product")
    product_url = Column(String(500), default="https://example.com")
    product_pitch = Column(Text, default="An automated AI tool that solves everyday bottlenecks.")
    target_audience = Column(String(255), default="Founders, Freelancers & Small Businesses")
    
    # Identifiants Reddit & X pour connexion de l'algorithme d'exploration
    reddit_username = Column(String(255), nullable=True, default="")
    reddit_password = Column(String(255), nullable=True, default="")
    twitter_handle = Column(String(255), nullable=True, default="")
    twitter_username = Column(String(255), nullable=True, default="")
    twitter_password = Column(String(255), nullable=True, default="")
    
    # Plans: 'FREE' (limit 5 leads), 'STARTER' ($29/mo), 'GROWTH' ($69/mo)
    plan = Column(String(50), default="FREE")
    is_active = Column(Boolean, default=True)
    is_founder = Column(Boolean, default=False)
    lemon_customer_id = Column(String(255), nullable=True)
    lemon_subscription_id = Column(String(255), nullable=True)
    subscription_status = Column(String(50), default="inactive") # 'active', 'past_due', 'cancelled'
    
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, default=datetime.utcnow)
    
    keywords = relationship("KeywordAlert", back_populates="user", cascade="all, delete-orphan")
    leads = relationship("Lead", back_populates="user", cascade="all, delete-orphan")
    billing_logs = relationship("BillingLog", back_populates="user", cascade="all, delete-orphan")

class KeywordAlert(Base):
    __tablename__ = "keyword_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    keyword = Column(String(255), nullable=False)
    platform = Column(String(50), default="reddit") # 'reddit' or 'twitter'
    subreddit = Column(String(100), default="SaaS") # e.g. 'SaaS', 'Entrepreneur', 'startups'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="keywords")

class Lead(Base):
    __tablename__ = "leads"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    platform = Column(String(50), default="reddit") # 'reddit' or 'twitter'
    subreddit = Column(String(100), default="SaaS")
    external_id = Column(String(100), index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    author = Column(String(100), default="redditor")
    original_url = Column(String(1000), nullable=False)
    
    # Psychologie & Score d'intention d'achat (0 - 100%)
    intent_score = Column(Integer, default=85) # 0 to 100
    intent_badge = Column(String(50), default="HOT") # 'HOT' (80-100%), 'WARM' (60-79%), 'INFO' (<60%)
    urgency_level = Column(String(50), default="HIGH") # 'HIGH', 'MEDIUM', 'LOW'
    pain_point_summary = Column(String(500), default="Looking for automated tool")
    
    # Réponse Stealth rédigée par l'IA (80% valeur + 20% plug avec lien de redirection)
    suggested_reply = Column(Text, nullable=False)
    
    # Suivi de conversion
    status = Column(String(50), default="NEW") # 'NEW', 'COPIED', 'CONVERTED', 'ARCHIVED'
    tracked_clicks = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="leads")
    clicks = relationship("ClickEvent", back_populates="lead", cascade="all, delete-orphan")

class ClickEvent(Base):
    __tablename__ = "click_events"
    
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    visitor_ip = Column(String(100), default="unknown")
    user_agent = Column(String(500), default="unknown")
    referrer = Column(String(500), default="direct")
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    lead = relationship("Lead", back_populates="clicks")

class BillingLog(Base):
    __tablename__ = "billing_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    event_name = Column(String(100), nullable=False)
    lemon_order_id = Column(String(100), nullable=True)
    amount_usd = Column(Float, default=0.0)
    currency = Column(String(10), default="USD")
    status = Column(String(50), default="success")
    payout_bank = Column(String(100), default="Lead Bank (Grey USD ••••9479)")
    payload_raw = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="billing_logs")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
