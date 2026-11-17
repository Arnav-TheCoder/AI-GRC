from pydantic import BaseModel, Field
from datetime import datetime

class AssessmentCreate(BaseModel):
    company_name: str = Field(min_length=1, max_length=200)
    model_name: str = Field(min_length=1, max_length=200)
    model_type: str = Field(default="Unknown", max_length=100)
    intended_use: str = Field(min_length=1, max_length=5000)
    deployment_context: str = Field(default="", max_length=5000)

class UploadOut(BaseModel):
    id: int
    upload_kind: str
    original_filename: str
    size_bytes: int
    inspection: dict
    class Config:
        from_attributes = True

class FindingOut(BaseModel):
    id: int
    framework: str
    function: str
    category: str
    title: str
    status: str
    severity: str
    evidence: str
    rationale: str
    source_type: str
    class Config:
        from_attributes = True

class AssessmentOut(BaseModel):
    id: int
    company_name: str
    model_name: str
    model_type: str
    intended_use: str
    deployment_context: str
    status: str
    created_at: datetime
    uploads: list[UploadOut] = []
    findings: list[FindingOut] = []
    class Config:
        from_attributes = True
