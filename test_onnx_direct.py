import onnxruntime as ort
import numpy as np
from transformers import AutoTokenizer
import os

# Use dynamic relative paths for Fedora
project_root = os.path.dirname(os.path.abspath(__file__))
onnx_path = os.path.join(project_root, "app", "artifacts", "codebert_multitask.onnx")

print(f"Loading ONNX artifact from: {onnx_path}")

try:
    session = ort.InferenceSession(onnx_path, providers=['CPUExecutionProvider'])
except Exception as e:
    print(f"Failed to load ONNX file. Ensure it is placed at {onnx_path}")
    raise e

tokenizer = AutoTokenizer.from_pretrained("microsoft/codebert-base")

COMPONENT_LABELS = [
    "browser_core", "extensions", "network", "other",
    "performance", "security", "storage", "ui"
]

bug_report = """Login button unresponsive on incorrect password input
Steps to Reproduce:
1. Go to the Login page
2. Enter a valid email but wrong password
3. Click the Login button

Expected Result:
An error message should appear saying "Invalid credentials"

Actual Result:
The button freezes and no feedback is shown to the user

Environment:
- Browser: Chrome
- OS: Windows 11
- App URL: http://localhost:5173"""

print("Running test for user bug report...")
inputs = tokenizer(bug_report, return_tensors="np", truncation=True, max_length=512, padding="max_length")
ort_inputs = {
    "input_ids": inputs["input_ids"].astype(np.int64),
    "attention_mask": inputs["attention_mask"].astype(np.int64)
}

outputs = session.run(None, ort_inputs)
output_names = [o.name for o in session.get_outputs()]
out_dict = dict(zip(output_names, outputs))

logits = np.squeeze(out_dict.get("component_logits", outputs[0]))
idx = np.argmax(logits)

# Convert to probabilities using Softmax to get the confidence score
e_x = np.exp(logits - np.max(logits))
probs = e_x / e_x.sum()
confidence = probs[idx]

priority_logits = np.squeeze(out_dict.get("priority_logits", outputs[1]))
p_idx = np.argmax(priority_logits)

PRIORITY_LABELS = ["P0", "P1", "P2", "P3"]

print(f"\n--- PREDICTION RESULTS ---")
print(f"Predicted Component: {COMPONENT_LABELS[idx]} (Index: {idx}, Confidence: {confidence:.4f})")
print(f"Predicted Priority: {PRIORITY_LABELS[p_idx]} (Index: {p_idx})")
print(f"Estimated Resolution: {out_dict.get('resolution_time', outputs[2]).item():.2f} days")