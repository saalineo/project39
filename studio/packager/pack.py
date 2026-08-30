import os
import tarfile
import argparse
import json
import subprocess
from datetime import datetime
from studio.packager.manifest import Manifest, hash_file
from studio.packager.gate import run_gate
from studio.packager.sign import sign_data

def get_git_commit():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("ascii").strip()
    except Exception:
        return "unknown-commit"

def pack(model_dir: str, lang: str):
    # Ensure artifacts directory exists
    artifacts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "artifacts"))
    os.makedirs(artifacts_dir, exist_ok=True)

    # Run Gate
    print("Running validation gate...")
    val_res = run_gate()
    print("Gate passed!")

    # Gather files (simulate G2P and tokenizer)
    os.makedirs(model_dir, exist_ok=True)
    onnx_path = os.path.join(model_dir, "model_int8.onnx")
    if not os.path.exists(onnx_path):
        raise FileNotFoundError(f"ONNX model not found at {onnx_path}")

    g2p_path = os.path.join(model_dir, f"g2p_{lang}.txt")
    if not os.path.exists(g2p_path):
        with open(g2p_path, "w") as f:
            f.write("dummy g2p")

    vocab_path = os.path.join(model_dir, "vocab.json")
    if not os.path.exists(vocab_path):
        with open(vocab_path, "w") as f:
            json.dump({"dummy": 0}, f)

    manifest_path = os.path.join(model_dir, "manifest.json")

    current_hashes = {
        "model.onnx": hash_file(onnx_path),
        "g2p.txt": hash_file(g2p_path),
        "vocab.json": hash_file(vocab_path)
    }

    if os.path.exists(manifest_path):
        print("Existing manifest found, verifying hashes...")
        with open(manifest_path, "r") as f:
            existing_manifest_data = json.load(f)
        for fname, expected_hash in existing_manifest_data["files"].items():
            # The keys might map differently depending on naming
            if fname == "model.onnx" and current_hashes["model.onnx"] != expected_hash:
                raise ValueError(f"Checksum mismatch for {fname}")
            if fname == "g2p.txt" and current_hashes["g2p.txt"] != expected_hash:
                raise ValueError(f"Checksum mismatch for {fname}")
            if fname == "vocab.json" and current_hashes["vocab.json"] != expected_hash:
                raise ValueError(f"Checksum mismatch for {fname}")

        manifest_json = json.dumps(existing_manifest_data, indent=2)
        # We will reuse the existing manifest object for audit log
        manifest = Manifest(**existing_manifest_data)
    else:
        # Create manifest
        manifest = Manifest(
            ir_version=8,
            opset=17,
            model_version="0.1.0",
            build_id=get_git_commit(),
            target_ort_version="1.17.0",
            files=current_hashes,
            validation=val_res
        )

        manifest_json = manifest.to_json()
        with open(manifest_path, "w") as f:
            f.write(manifest_json)

    # Sign manifest hash
    signature = sign_data(manifest_json.encode('utf-8'))
    sig_path = os.path.join(model_dir, "manifest.sig")
    with open(sig_path, "wb") as f:
        f.write(signature)

    # Pack into .pkg (tar)
    pkg_name = f"model_{lang}.pkg"
    pkg_path = os.path.join(artifacts_dir, pkg_name)
    with tarfile.open(pkg_path, "w") as tar:
        tar.add(onnx_path, arcname="model.onnx")
        tar.add(g2p_path, arcname="g2p.txt")
        tar.add(vocab_path, arcname="vocab.json")
        tar.add(manifest_path, arcname="manifest.json")
        tar.add(sig_path, arcname="manifest.sig")

    print(f"Artifact packaged successfully at {pkg_path}")

    # Audit log
    audit_log_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ci", "audit-log.jsonl"))
    with open(audit_log_path, "a") as f:
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "build_id": manifest.build_id,
            "model_version": manifest.model_version,
            "opset": manifest.opset,
            "validation": manifest.validation
        }
        f.write(json.dumps(audit_entry) + "\n")
    print(f"Audit log updated at {audit_log_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Path to model directory")
    parser.add_argument("--lang", required=True, help="Language code")
    args = parser.parse_args()
    pack(args.model, args.lang)
