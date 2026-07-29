from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime

class Base(DeclarativeBase): pass

class SyncRun(Base):
    __tablename__="sync_run"
    id:Mapped[int]=mapped_column(BigInteger,primary_key=True)
    source:Mapped[str]=mapped_column(String(80),index=True)
    status:Mapped[str]=mapped_column(String(30),index=True)
    started_at:Mapped[datetime]=mapped_column(DateTime(timezone=True))
    finished_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
    records_read:Mapped[int]=mapped_column(Integer,default=0)
    records_changed:Mapped[int]=mapped_column(Integer,default=0)
    details:Mapped[dict]=mapped_column(JSON,default=dict)

class Snapshot(Base):
    __tablename__="snapshot"
    __table_args__=(UniqueConstraint("entity","external_key","fingerprint"),)
    id:Mapped[int]=mapped_column(BigInteger,primary_key=True)
    entity:Mapped[str]=mapped_column(String(100),index=True)
    external_key:Mapped[str]=mapped_column(String(180),index=True)
    fingerprint:Mapped[str]=mapped_column(String(64),index=True)
    payload:Mapped[dict]=mapped_column(JSON)
    captured_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),index=True)

class DetectedChange(Base):
    __tablename__="detected_change"
    id:Mapped[int]=mapped_column(BigInteger,primary_key=True)
    entity:Mapped[str]=mapped_column(String(100),index=True)
    external_key:Mapped[str]=mapped_column(String(180),index=True)
    field:Mapped[str]=mapped_column(String(120))
    before:Mapped[dict|None]=mapped_column(JSON,nullable=True)
    after:Mapped[dict|None]=mapped_column(JSON,nullable=True)
    detected_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),index=True)

class Alert(Base):
    __tablename__="alert"
    id:Mapped[int]=mapped_column(BigInteger,primary_key=True)
    type:Mapped[str]=mapped_column(String(60),index=True)
    level:Mapped[str]=mapped_column(String(20),index=True)
    title:Mapped[str]=mapped_column(String(240))
    message:Mapped[str]=mapped_column(Text)
    context:Mapped[dict]=mapped_column(JSON,default=dict)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),index=True)
    resolved:Mapped[bool]=mapped_column(Boolean,default=False,index=True)
