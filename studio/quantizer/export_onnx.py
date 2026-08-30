import torch
import onnx
import argparse
import os

class DummyTTS(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = torch.nn.Linear(10, 50)
        self.relu = torch.nn.ReLU()
        self.fc2 = torch.nn.Linear(50, 10)

    def forward(self, x):
        return self.fc2(self.relu(self.fc1(x)))

def export_model(output_path, opset_version=14):
    model = DummyTTS()
    model.eval()
    dummy_input = torch.randn(1, 10)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    torch.onnx.export(
        model,
        dummy_input,
        output_path,
        export_params=True,
        opset_version=opset_version,
        do_constant_folding=True,
        input_names=['input'],
        output_names=['output'],
        dynamic_axes={'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}}
    )
    
    onnx_model = onnx.load(output_path)
    print(f"Exported to {output_path}")
    print(f"IR Version: {onnx_model.ir_version}")
    print(f"Opset Version: {onnx_model.opset_import[0].version}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=str, default="../../models/model_fp32.onnx")
    parser.add_argument("--opset", type=int, default=14)
    args = parser.parse_args()
    export_model(args.output, args.opset)
