from studio.validation.wer import evaluate_wer
from studio.validation.mos import evaluate_mos

WER_TOLERANCE = 0.05
MOS_TOLERANCE = 0.1

def run_gate():
    wer_res = evaluate_wer()
    mos_res = evaluate_mos()

    wer_delta = round(wer_res["wer_delta"], 5)
    mos_delta = round(mos_res["mos_delta"], 5)

    passed = (wer_delta <= WER_TOLERANCE) and (mos_delta <= MOS_TOLERANCE)
    
    if not passed:
        raise RuntimeError(f"Gate failed! WER delta: {wer_delta} (limit: {WER_TOLERANCE}), MOS delta: {mos_delta} (limit: {MOS_TOLERANCE})")
    
    return {
        "wer_delta": wer_delta,
        "mos_delta": mos_delta,
        "wer_fp32": wer_res["wer_fp32"],
        "wer_int8": wer_res["wer_int8"],
        "mos_fp32": mos_res["mos_fp32"],
        "mos_int8": mos_res["mos_int8"]
    }
