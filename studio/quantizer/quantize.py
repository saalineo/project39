import onnx
from onnxruntime.quantization import quantize_dynamic, QuantType
import argparse
import os

def quantize_model(input_path, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    quantize_dynamic(
        model_input=input_path,
        model_output=output_path,
        weight_type=QuantType.QInt8,
    )
    print(f"Quantized model saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, default="../../models/model_fp32.onnx")
    parser.add_argument("--output", type=str, default="../../models/model_int8.onnx")
    args = parser.parse_args()
    quantize_model(args.input, args.output)
