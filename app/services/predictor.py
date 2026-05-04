import os
import asyncio
import numpy as np
import onnxruntime as ort
from transformers import AutoTokenizer
from typing import Dict, Any

class PredictorService:
    # Pre-defined labels matching your system architecture
    COMPONENT_LABELS = [
        "browser_core", "extensions", "network", "other",
        "performance", "security", "storage", "ui"
    ]
    PRIORITY_LABELS = ["P0", "P1", "P2", "P3"]

    def __init__(self):
        # avoid heavy IO during import
        self.session = None
        self.tokenizer = None
        self._initialized = False

    def _initialize_sync(self):
        """Synchronous initialization that performs heavy I/O."""
        artifact_path = os.path.join(os.path.dirname(__file__), "../artifacts/codebert_multitask.onnx")

        # Initialize the ONNX session
        self.session = ort.InferenceSession(
            artifact_path,
            providers=['CPUExecutionProvider']
        )

        # Load the CodeBERT tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained("microsoft/codebert-base")
        self._initialized = True

    async def initialize(self):
        """Async entrypoint to initialize heavy resources in a thread."""
        if not self._initialized:
            await asyncio.to_thread(self._initialize_sync)

    def _ensure_initialized(self):
        if not self._initialized:
            raise RuntimeError("PredictorService not initialized. Call await predictor.initialize() at app startup.")

    def _softmax(self, x: np.ndarray) -> np.ndarray:
        e_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
        return e_x / e_x.sum(axis=-1, keepdims=True)

    def _run_inference(self, text: str) -> Dict[str, Any]:
        """Synchronous execution of the ONNX graph with diagnostics."""
        self._ensure_initialized()

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

        # Map outputs by name
        output_names = [o.name for o in self.session.get_outputs()]
        out_dict = dict(zip(output_names, outputs))

        comp_out = out_dict.get("component_logits")
        component_logits = np.squeeze(comp_out) if comp_out is not None else np.zeros(len(self.COMPONENT_LABELS))

        prio_out = out_dict.get("priority_logits")
        priority_logits = np.squeeze(prio_out) if prio_out is not None else np.zeros(len(self.PRIORITY_LABELS))

        res_out = out_dict.get("resolution_time")
        resolution_time = res_out.item() if res_out is not None else 0.0

        att_out = out_dict.get("cls_attention")
        attention_weights = np.squeeze(att_out) if att_out is not None else []

        component_probs = self._softmax(component_logits)
        component_idx = int(np.argmax(component_probs))

        if component_idx < len(self.COMPONENT_LABELS):
            predicted_component = self.COMPONENT_LABELS[component_idx]
        else:
            predicted_component = "other"

        priority_idx = int(np.argmax(self._softmax(priority_logits)))
        predicted_priority = self.PRIORITY_LABELS[priority_idx]

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

    async def predict_async(self, text: str) -> Dict[str, Any]:
        """Offloads the CPU-heavy inference to a separate thread."""
        self._ensure_initialized()
        return await asyncio.to_thread(self._run_inference, text)


# Global instance is safe to import; it does NOT perform heavy I/O until initialize() is called.
predictor = PredictorService()
