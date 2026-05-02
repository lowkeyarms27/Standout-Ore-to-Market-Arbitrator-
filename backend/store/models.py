from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from backend.store.database import Base


class PriceSnapshot(Base):
    __tablename__ = "price_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    source = Column(String(32))
    symbol = Column(String(16), index=True)
    value = Column(Float)
    unit = Column(String(32))
    raw_json = Column(Text)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    trigger_type = Column(String(64))
    severity = Column(String(16))
    message = Column(Text)
    trigger_data = Column(Text)
    resolved = Column(Boolean, default=False)
    resolved_by = Column(Integer, nullable=True)


class Decision(Base):
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    alert_id = Column(Integer, nullable=True)
    economist_recommendation = Column(Text)
    challenger_review = Column(Text)
    final_action = Column(String(32))
    action_description = Column(Text)
    executed = Column(Boolean, default=False)
    execution_result = Column(Text, nullable=True)


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    report_type = Column(String(32))
    title = Column(String(256))
    content_json = Column(Text)
    pdf_path = Column(String(512), nullable=True)
