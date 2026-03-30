from app.database.client import db_state


class LogRepository:

    @staticmethod
    async def insert_prediction(
            issue_title: str,
            description: str,
            predicted_component: str,
            confidence_score: float,
            execution_time_ms: float
    ) -> str:
        """
        Persists the input payload and inference results to db
        """

        query = """
                INSERT INTO prediction_logs
                (issue_title, description, predicted_component, confidence_score, execution_time_ms)
                VALUES ($1, $2, $3, $4, $5) RETURNING id; \
                """

        if db_state.pool is None:
            raise RuntimeError("Database pool is not initialized.")

        try:
            async with db_state.pool.acquire() as connection:
                log_id = await connection.fetchval(
                    query,
                    issue_title,
                    description,
                    predicted_component,
                    confidence_score,
                    execution_time_ms
                )
            return str(log_id)
        except Exception as e:
            raise RuntimeError(f"Database insertion failed: {e}")