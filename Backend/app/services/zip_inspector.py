import json
import os
import zipfile
from pathlib import PurePosixPath

MAX_UNCOMPRESSED_BYTES = 500 * 1024 * 1024
MAX_COMPRESSION_RATIO = 200

INTERESTING_NAMES = {
    "config.json", "model_config.json", "requirements.txt", "pyproject.toml",
    "environment.yml", "conda.yaml", "metadata.json", "README.md",
    "model card.md", "modelcard.md"
}
MODEL_EXTENSIONS = {".pt", ".pth", ".onnx", ".h5", ".keras", ".safetensors",
                    ".pkl", ".joblib", ".pb", ".tflite", ".bin"}

def inspect_zip(path: str, max_files: int) -> dict:
    result = {
        "safe_to_extract": False,
        "archive_valid": False,
        "file_count": 0,
        "total_uncompressed_bytes": 0,
        "model_files": [],
        "configuration_files": [],
        "dependency_files": [],
        "top_level_items": [],
        "warnings": [],
        "inspection_scope": "Archive metadata only. No files were extracted or executed."
    }
    if not zipfile.is_zipfile(path):
        result["warnings"].append("The uploaded file is not a valid ZIP archive.")
        return result

    try:
        with zipfile.ZipFile(path) as zf:
            infos = zf.infolist()
            result["archive_valid"] = True
            result["file_count"] = len(infos)
            if len(infos) > max_files:
                result["warnings"].append(f"Archive exceeds the {max_files}-entry limit.")
                return result

            seen_top = set()
            total = 0
            for info in infos:
                name = info.filename
                normalized = name.replace("\\", "/")
                parts = PurePosixPath(normalized).parts
                if normalized.startswith("/") or ".." in parts or (parts and ":" in parts[0]):
                    result["warnings"].append(f"Unsafe archive path rejected: {name[:160]}")
                    return result
                if info.flag_bits & 0x1:
                    result["warnings"].append("Encrypted ZIP entries are not supported.")
                    return result
                if info.file_size < 0 or info.compress_size < 0:
                    result["warnings"].append("Archive contains invalid size metadata.")
                    return result
                total += info.file_size
                if info.file_size and info.compress_size == 0:
                    result["warnings"].append("Suspicious zero-size compressed entry.")
                    return result
                if info.compress_size and info.file_size / info.compress_size > MAX_COMPRESSION_RATIO:
                    result["warnings"].append(f"Suspicious compression ratio: {name[:120]}")
                    return result

                if parts:
                    seen_top.add(parts[0])
                suffix = os.path.splitext(name)[1].lower()
                base = os.path.basename(name).lower()
                if suffix in MODEL_EXTENSIONS:
                    result["model_files"].append(name[:240])
                if base in INTERESTING_NAMES:
                    result["configuration_files"].append(name[:240])
                if base in {"requirements.txt", "pyproject.toml", "environment.yml", "conda.yaml"}:
                    result["dependency_files"].append(name[:240])

            if total > MAX_UNCOMPRESSED_BYTES:
                result["warnings"].append("Archive expands beyond the 500 MB inspection limit.")
                return result

            result["total_uncompressed_bytes"] = total
            result["top_level_items"] = sorted(seen_top)[:100]
            result["safe_to_extract"] = True
            result["warnings"].append(
                "Metadata inspection is not malware detection and does not prove that model files are safe."
            )
            return result
    except (zipfile.BadZipFile, OSError, RuntimeError) as exc:
        result["warnings"].append(f"Could not inspect archive: {type(exc).__name__}")
        return result
