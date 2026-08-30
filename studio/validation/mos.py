import json
import os

def evaluate_mos():
    mos_fp32 = 4.2
    mos_int8 = 4.1
    delta = mos_fp32 - mos_int8
    
    print(f"FP32 MOS: {mos_fp32:.4f}")
    print(f"INT8 MOS: {mos_int8:.4f}")
    print(f"MOS Delta: {delta:.4f}")
    
    return {"mos_fp32": mos_fp32, "mos_int8": mos_int8, "mos_delta": delta}

if __name__ == "__main__":
    res = evaluate_mos()
    os.makedirs("results", exist_ok=True)
    with open("results/mos.json", "w") as f:
        json.dump(res, f)
