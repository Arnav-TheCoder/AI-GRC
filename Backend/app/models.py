from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

def utcnow():
    return datetime.now(timezone.utc)

class Assessment(Base):
    __tablename__ = "assessments"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    company_name: Mapped[str] = mapped_column(String(200))
    model_name: Mapped[str] = mapped_column(String(200))
    model_type: Mapped[str] = mapped_column(String(100), default="Unknown")
    intended_use: Mapped[str] = mapped_column(Text)
    deployment_context: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(40), default="Intake")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    uploads: Mapped[list["Upload"]] = relationship(back_populates="assessment", cascade="all, delete-orphan")
    findings: Mapped[list["Finding"]] = relationship(back_populates="assessment", cascade="all, delete-orphan")

class Upload(Base):
    __tablename__ = "uploads"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessments.id"))
    upload_kind: Mapped[str] = mapped_column(String(40))
    original_filename: Mapped[str] = mapped_column(String(255))
    stored_filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(150), default="")
    size_bytes: Mapped[int] = mapped_column(Integer)
    inspection_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    assessment: Mapped[Assessment] = relationship(back_populates="uploads")

    @property
    def inspection(self) -> dict:
        import json
        try:
            return json.loads(self.inspection_json or "{}")
        except (TypeError, ValueError):
            return {}


class Finding(Base):
    __tablename__ = "assessment_findings"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessments.id"))
    framework: Mapped[str] = mapped_column(String(80), default="NIST AI RMF 1.0")
    function: Mapped[str] = mapped_column(String(20))
    category: Mapped[str] = mapped_column(String(180))
    title: Mapped[str] = mapped_column(String(240))
    status: Mapped[str] = mapped_column(String(40))
    severity: Mapped[str] = mapped_column(String(30), default="Informational")
    evidence: Mapped[str] = mapped_column(Text, default="")
    rationale: Mapped[str] = mapped_column(Text, default="")
    source_type: Mapped[str] = mapped_column(String(40), default="technical_inspection")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    assessment: Mapped[Assessment] = relationship(back_populates="findings")
