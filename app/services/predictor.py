import os
import asyncio
import numpy as np
import onnxruntime as ort
from transformers import AutoTokenizer
from typing import Dict, Any
import traceback

class PredictorService:
    _instance = None

    # Pre-defined labels matching your system architecture
    COMPONENT_LABELS = [
        "browser_core", "extensions", "network", "other",
        "performance", "security", "storage", "ui"
    ]
    PRIORITY_LABELS = ["P0", "P1", "P2", "P3"]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PredictorService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Loads artifacts into memory once."""
        artifact_path = os.path.join(os.path.dirname(__file__), "../artifacts/codebert_multitask.onnx")

        # Initialize the ONNX session
        self.session = ort.InferenceSession(
            artifact_path,
            providers=['CPUExecutionProvider']
        )

        # Load the CodeBERT tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained("microsoft/codebert-base")

    def _softmax(self, x: np.ndarray) -> np.ndarray:
        e_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
        return e_x / e_x.sum(axis=-1, keepdims=True)

    def _run_inference(self, text: str) -> Dict[str, Any]:
        """Synchronous execution of the ONNX graph with diagnostics."""
        try:
            inputs = self.tokenizer(
                text,
                return_tensors="np",
                truncation=True,
                max_length=512,
                padding="max_length"
            )

            ort_inputs = {
                "input_ids": inputs["input_ids"].astype(np.int64),
                "attention_mask": inputs["attention_mask"].astype(np.int64)
            }

            outputs = self.session.run(None, ort_inputs)
            num_outputs = len(outputs)

            # --- DIAGNOSTIC LOGGING ---
            print("\n=== ONNX OUTPUT DIAGNOSTICS ===")
            print(f"Total outputs returned: {num_outputs}")
            for i, out in enumerate(outputs):
                print(f"Output {i} shape: {out.shape if hasattr(out, 'shape') else type(out)}")
            print("===============================\n")

            # 1. Component Logits
            if num_outputs > 0:
                component_logits = np.squeeze(outputs[0])
            else:
                component_logits = np.zeros(len(self.COMPONENT_LABELS))

            # 2. Priority Logits
            if num_outputs > 1:
                priority_logits = np.squeeze(outputs[1])
            else:
                priority_logits = np.zeros(len(self.PRIORITY_LABELS))

            # 3. Resolution Time
            if num_outputs > 2:
                resolution_time = outputs[2].item()
            else:
                resolution_time = 0.0

            # 4. Attention Weights
            if num_outputs > 3:
                attention_weights = np.squeeze(outputs[3])
            else:
                attention_weights = []

            # Calculate component
            component_probs = self._softmax(component_logits)
            component_idx = int(np.argmax(component_probs))

            # Safe boundary lookup to prevent IndexError
            if component_idx < len(self.COMPONENT_LABELS):
                predicted_component = self.COMPONENT_LABELS[component_idx]
            else:
                print(f"Warning: Model predicted unknown index {component_idx}. Defaulting to 'other'.")
                predicted_component = "other"

            confidence_score = float(component_probs[component_idx])

            # Calculate priority
            priority_idx = int(np.argmax(self._softmax(priority_logits)))
            predicted_priority = self.PRIORITY_LABELS[priority_idx]

            # Package tokens (converting numpy array to native python list first)
            tokens = self.tokenizer.convert_ids_to_tokens(inputs["input_ids"][0].tolist())

            return {
                "predicted_component": predicted_component,
                "confidence_score": float(component_probs[component_idx]),
                "priority": predicted_priority,
                "resolution_time_days": max(0.0, resolution_time),
                "attention_weights": {
                    "tokens": tokens,
                    "weights": attention_weights.tolist() if isinstance(attention_weights, np.ndarray) else []
                }
            }

        except Exception as e:
            # Print the exact line number and error to the console
            import traceback
            print(f"\n--- FATAL TRACEBACK ---\n{traceback.format_exc()}-----------------------\n")
            raise e

    async def predict_async(self, text: str) -> Dict[str, Any]:
        """Offloads the CPU-heavy inference to a separate thread."""
        return await asyncio.to_thread(self._run_inference, text)


# Instantiate a global instance to be imported by the routers
predictor = PredictorService()