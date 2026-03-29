import os
import joblib
from preprocessor import TextPreprocessor

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTIFACTS_DIR = os.path.join(BASE_DIR, "artifacts")


class BugReportPredictor:
    """Singleton service for inference execution."""

    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.label_encoder = None
        self.is_loaded = False

    def load_artifacts(self):
        """Deserializes pipeline artifacts into memory."""
        if self.is_loaded:
            return

        try:
            self.model = joblib.load(os.path.join(ARTIFACTS_DIR, "model.joblib"))
            self.vectorizer = joblib.load(os.path.join(ARTIFACTS_DIR, "vectorizer.joblib"))
            self.label_encoder = joblib.load(os.path.join(ARTIFACTS_DIR, "label_encoder.joblib"))
            self.is_loaded = True
        except Exception as e:
            raise RuntimeError(f"Artifact deserialization failed: {e}")

    def predict(self, title: str, description: str) -> dict:
        """Executes preprocessing, vectorization, and inference sequence."""
        if not self.is_loaded:
            raise RuntimeError("Artifacts uninitialized. Execute load_artifacts().")

        text_payload = f"{title} {description}"
        cleaned_text = TextPreprocessor.clean_text(text_payload)

        features = self.vectorizer.transform([cleaned_text])

        prediction_idx = self.model.predict(features)[0]
        predicted_label = self.label_encoder.inverse_transform([prediction_idx])[0]

        confidence = 0.0
        if hasattr(self.model, "predict_proba"):
            probabilities = self.model.predict_proba(features)[0]
            confidence = float(max(probabilities))

        return {
            "predicted_component": predicted_label,
            "confidence_score": round(confidence, 4)
        }


predictor_service = BugReportPredictor()