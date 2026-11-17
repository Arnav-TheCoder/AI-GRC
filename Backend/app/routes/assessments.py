import json
import os
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Assessment, Upload
from ..schemas import AssessmentCreate, AssessmentOut
from ..config import settings
from ..services.zip_inspector import inspect_zip
from ..services.assessment_engine import run_preliminary_assessment
from ..services.dataset_inspector import inspect_csv
from ..services.dataset_inspector import inspect_csv

router = APIRouter(prefix="/api/assessments", tags=["assessments"])
ALLOWED_DATASET_KINDS = {"training", "validation", "test"}

def get_assessment_or_404(db: Session, assessment_id: int):
    item = db.get(Assessment, assessment_id)
    if not item:
        raise HTTPException(404, "Assessment not found")
    return item

def save_upload(file: UploadFile, assessment_id: int, kind: str):
    os.makedirs(settings.upload_dir, exist_ok=True)
    max_bytes = settings.max_upload_mb * 1024 * 1024
    stored = f"{assessment_id}_{kind}_{uuid.uuid4().hex}"
    destination = Path(settings.upload_dir) / stored
    size = 0
    try:
        with destination.open("wb") as out:
            while chunk := file.file.read(1024 * 1024):
                size += len(chunk)
                if size > max_bytes:
                    raise HTTPException(413, f"File exceeds {settings.max_upload_mb} MB limit")
                out.write(chunk)
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    return stored, size, str(destination)

@router.post("", response_model=AssessmentOut)
def create_assessment(payload: AssessmentCreate, db: Session = Depends(get_db)):
    item = Assessment(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.get("", response_model=list[AssessmentOut])
def list_assessments(db: Session = Depends(get_db)):
    return db.query(Assessment).order_by(Assessment.id.desc()).all()

@router.get("/{assessment_id}", response_model=AssessmentOut)
def get_assessment(assessment_id: int, db: Session = Depends(get_db)):
    return get_assessment_or_404(db, assessment_id)

@router.post("/{assessment_id}/model", response_model=AssessmentOut)
def upload_model(assessment_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    item = get_assessment_or_404(db, assessment_id)
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(400, "Please upload a .zip file.")
    stored, size, path = save_upload(file, assessment_id, "model")
    inspection = inspect_zip(path, settings.max_zip_files)
    record = Upload(
        assessment_id=assessment_id, upload_kind="model",
        original_filename=Path(file.filename).name[:255], stored_filename=stored,
        content_type=file.content_type or "", size_bytes=size,
        inspection_json=json.dumps(inspection)
    )
    db.add(record)
    item.status = "Model uploaded"
    db.commit()
    db.refresh(item)
    return item

@router.post("/{assessment_id}/datasets/{kind}", response_model=AssessmentOut)
def upload_dataset(assessment_id: int, kind: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    item = get_assessment_or_404(db, assessment_id)
    if kind not in ALLOWED_DATASET_KINDS:
        raise HTTPException(400, "Dataset kind must be training, validation or test.")
    if not file.filename or Path(file.filename).suffix.lower() not in {".csv"}:
        raise HTTPException(400, "For this prototype, datasets must be CSV files.")
    stored, size, path = save_upload(file, assessment_id, kind)
    dataset_inspection = inspect_csv(path)
    record = Upload(
        assessment_id=assessment_id, upload_kind=kind,
        original_filename=Path(file.filename).name[:255], stored_filename=stored,
        content_type=file.content_type or "", size_bytes=size,
        inspection_json=json.dumps(dataset_inspection)
    )
    db.add(record)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{assessment_id}/report")
def get_assessment_report(assessment_id: int, db: Session = Depends(get_db)):
    item = get_assessment_or_404(db, assessment_id)
    findings = item.findings or []
    counts = {"pass": 0, "fail": 0, "insufficient_evidence": 0}
    for finding in findings:
        if finding.status in counts:
            counts[finding.status] += 1
    by_function = {}
    for finding in findings:
        by_function.setdefault(finding.function, []).append({
            "id": finding.id, "category": finding.category, "title": finding.title,
            "status": finding.status, "severity": finding.severity,
            "evidence": finding.evidence, "rationale": finding.rationale,
            "source_type": finding.source_type,
        })
    return {
        "assessment_id": item.id, "company_name": item.company_name,
        "model_name": item.model_name, "model_type": item.model_type,
        "intended_use": item.intended_use, "deployment_context": item.deployment_context,
        "status": item.status, "created_at": item.created_at,
        "framework": "NIST AI RMF 1.0", "finding_counts": counts,
        "total_findings": len(findings), "by_function": by_function,
        "uploads": [{"kind": u.upload_kind, "filename": u.original_filename,
                      "size_bytes": u.size_bytes, "inspection": u.inspection}
                     for u in item.uploads],
        "limitations": [
            "This prototype performs limited metadata and intake checks; it does not certify NIST conformity.",
            "A recognized model file extension does not validate model contents, accuracy or behavior.",
            "CSV inspection is structural profiling only; it does not establish data quality, representativeness or fairness.",
            "No model code is executed and no malware scan is performed.",
            "User-provided declarations are not independently verified."
        ]
    }


@router.post("/{assessment_id}/run", response_model=AssessmentOut)
def run_assessment(assessment_id: int, db: Session = Depends(get_db)):
    item = get_assessment_or_404(db, assessment_id)
    if not any(upload.upload_kind == "model" for upload in item.uploads):
        raise HTTPException(400, "Upload a model ZIP before running the assessment.")
    run_preliminary_assessment(db, item)
    db.refresh(item)
    return item
