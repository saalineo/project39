import json
import os
import subprocess
import sys

def main():
    print("Running Model Quantization POC...")

    python_exe = sys.executable

    # Export FP32
    subprocess.run([python_exe, "../quantizer/export_onnx.py", "--output", "../../models/model_fp32.onnx"], check=True)

    # Quantize to INT8
    subprocess.run([python_exe, "../quantizer/quantize.py", "--input", "../../models/model_fp32.onnx", "--output", "../../models/model_int8.onnx"], check=True)

    # Evaluate WER
    subprocess.run([python_exe, "wer.py"], check=True)

    # Evaluate MOS
    subprocess.run([python_exe, "mos.py"], check=True)

    # Check Gate
    with open("results/wer.json") as f:
        wer_res = json.load(f)
    with open("results/mos.json") as f:
        mos_res = json.load(f)

    wer_delta = wer_res["wer_delta"]
    mos_delta = mos_res["mos_delta"]

    results = {
        "wer_delta": wer_delta,
        "mos_delta": mos_delta,
        "pass": wer_delta <= 0.01 and mos_delta <= 0.3
    }

    with open("results/m0-poc-en.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\nM0 Results:", results)
    if not results["pass"]:
        print("M0 Gate FAILED")
        exit(1)
    else:
        print("M0 Gate PASSED")

if __name__ == "__main__":
    main()
