from app.database.client import supabase_client


class LogRepository:

    TABLE_NAME = "prediction_logs"

    @staticmethod
    def insert_prediction(
            issue_title: str,
            description: str,
            predicted_component: str,
            confidence_score: float,
            execution_time_ms: float
    ) -> dict:
        """
        Persists the input payload and inference results to db
        """
        payload = {
            "issue_title": issue_title,
            "description": description,
            "predicted_component": predicted_component,
            "confidence_score": confidence_score,
            "execution_time_ms": execution_time_ms
        }

        try:
            response = supabase_client.table(LogRepository.TABLE_NAME).insert(payload).execute()
            if not response.data:
                raise RuntimeError("Supabase insertion returned empty data.")
            return response.data[0]
        except Exception as e:
            # might log this error but allow the API response to proceed
            raise RuntimeError(f"Database insertion failed: {e}")