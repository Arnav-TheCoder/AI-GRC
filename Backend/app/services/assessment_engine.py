from sqlalchemy.orm import Session
from ..models import Assessment, Finding, Upload


def _finding(assessment_id: int, function: str, category: str, title: str,
             status: str, severity: str, evidence: str, rationale: str,
             source_type: str = "technical_inspection") -> Finding:
    return Finding(
        assessment_id=assessment_id, framework="NIST AI RMF 1.0",
        function=function, category=category, title=title, status=status,
        severity=severity, evidence=evidence, rationale=rationale,
        source_type=source_type,
    )


def run_preliminary_assessment(db: Session, assessment: Assessment) -> list[Finding]:
    """Run limited, repeatable checks from submitted metadata. Does not certify compliance."""
    db.query(Finding).filter(Finding.assessment_id == assessment.id).delete()
    results: list[Finding] = []
    model_upload = (
        db.query(Upload)
        .filter(Upload.assessment_id == assessment.id, Upload.upload_kind == "model")
        .order_by(Upload.id.desc()).first()
    )

    if not model_upload:
        results.append(_finding(assessment.id, "MAP", "AI system context",
            "Model package has not been uploaded", "insufficient_evidence", "High",
            "No model ZIP upload is associated with this assessment.",
            "A model package is needed for the limited technical checks in this prototype."))
    else:
        info = model_upload.inspection or {}
        valid = bool(info.get("archive_valid"))
        results.append(_finding(assessment.id, "MAP", "AI system context",
            "ZIP archive validity", "pass" if valid else "fail", "High",
            f"archive_valid={valid}; file_count={info.get('file_count', 0)}",
            "This checks whether the uploaded file can be read as a ZIP archive. It is not a malware scan."))

        safe = bool(info.get("safe_to_extract"))
        results.append(_finding(assessment.id, "MANAGE", "Technical intake safeguards",
            "Archive structure checks", "pass" if safe else "fail", "High",
            "; ".join(info.get("warnings", [])) or "No ZIP structure warnings were recorded.",
            "The inspector checks archive paths, encryption, size limits and compression ratios. Passing does not prove the files are safe."))

        model_files = info.get("model_files", [])
        results.append(_finding(assessment.id, "MAP", "AI system context",
            "Recognizable model artifact found", "pass" if model_files else "insufficient_evidence", "Medium",
            ", ".join(model_files[:20]) if model_files else "No recognized model file extension was found.",
            "A recognized extension is only a file-format clue. The model contents and behavior have not been validated."))

        config_files = info.get("configuration_files", [])
        dependency_files = info.get("dependency_files", [])
        found_support = bool(config_files or dependency_files)
        results.append(_finding(assessment.id, "MAP", "AI system documentation",
            "Configuration or dependency documentation", "pass" if found_support else "insufficient_evidence", "Low",
            ", ".join((config_files + dependency_files)[:20]) if found_support else "No recognized configuration or dependency manifest was found.",
            "The presence of these files does not establish that documentation is complete or accurate."))

    dataset_uploads = [u for u in assessment.uploads if u.upload_kind in {"training", "validation", "test"}]
    if not dataset_uploads:
        results.append(_finding(assessment.id, "MAP", "Data characteristics and provenance",
            "Evaluation dataset evidence not supplied", "insufficient_evidence", "Medium",
            "No training, validation or test CSV was uploaded.",
            "Dataset provenance, representativeness, quality and suitability cannot be assessed from model metadata alone.", "technical_inspection"))
    else:
        for upload in dataset_uploads:
            profile = upload.inspection or {}
            status = "pass" if profile.get("analysis_status") == "completed" and profile.get("row_count", 0) > 0 else "insufficient_evidence"
            cols = profile.get("columns", [])
            missing_cols = [c["name"] for c in cols if c.get("missing_count", 0) > 0]
            evidence = f"{upload.upload_kind}: {profile.get('row_count', 0)} rows; {profile.get('column_count', 0)} columns. "
            evidence += f"Columns: {', '.join(c.get('name', '') for c in cols[:25]) or 'none detected'}. "
            evidence += f"Columns with missing values: {', '.join(missing_cols[:20]) or 'none detected in inspected rows'}."
            results.append(_finding(assessment.id, "MAP", "Data characteristics and provenance",
                f"{upload.upload_kind.title()} dataset structural profile", status, "Medium", evidence,
                "This is a structural CSV profile only. It does not verify data provenance, consent, representativeness, label quality or fairness.", "technical_inspection"))

    declaration = (assessment.intended_use or "").strip()
    results.append(_finding(assessment.id, "MAP", "Intended purpose and deployment context",
        "Intended use supplied by organization", "insufficient_evidence", "Medium",
        declaration[:1500] if declaration else "No intended use was supplied.",
        "This is a user-provided declaration. The organization must provide supporting context and identify affected people, decisions and foreseeable misuse.",
        "user_declaration"))

    questions = [
        ("GOVERN", "Governance and accountability", "Who owns this AI system, approves changes and is accountable for its risks?"),
        ("MAP", "Stakeholders and impact", "Who may be affected by the model's outputs, including people who do not directly use it?"),
        ("MAP", "Data provenance and context", "What are the data sources, collection conditions, permissions and known limitations?"),
        ("MEASURE", "Performance and evaluation", "What evaluation metrics, test datasets and acceptance thresholds were used?"),
        ("MEASURE", "Fairness and bias", "Which groups were evaluated for differences in model performance, and what were the results?"),
        ("MEASURE", "Privacy and security", "How are personal or sensitive data protected during training, inference and storage?"),
        ("MEASURE", "Robustness and safety", "How was the model tested for failures, unusual inputs, misuse and unsafe outputs?"),
        ("MANAGE", "Monitoring and incident response", "How will performance be monitored, incidents handled and the model withdrawn if necessary?"),
    ]
    for function, category, question in questions:
        results.append(_finding(assessment.id, function, category,
            f"Evidence required: {category}", "insufficient_evidence", "Medium",
            f"Assessment question: {question}",
            "No supporting answer or evidence has been collected for this assessment area yet.",
            "pending_questionnaire"))

    db.add_all(results)
    assessment.status = "Preliminary assessment complete"
    db.commit()
    for item in results:
        db.refresh(item)
    return results
