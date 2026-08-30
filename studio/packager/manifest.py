import hashlib
from dataclasses import dataclass, asdict
import json
import os

@dataclass
class Manifest:
    ir_version: int
    opset: int
    model_version: str
    build_id: str
    target_ort_version: str
    files: dict  # file_name -> sha256
    validation: dict  # wer_delta, mos_delta, pass

    def to_json(self):
        return json.dumps(asdict(self), indent=2)

def hash_file(filepath: str) -> str:
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()
