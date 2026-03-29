import re


class TextPreprocessor:

    @staticmethod
    def clean_text(text: str) -> str:
        if not text:
            return ""

        # Convert to lowercase
        text = text.lower()

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)

        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)

        # Remove code blocks (assuming markdown-style backticks)
        text = re.sub(r'```.*?```', ' ', text, flags=re.DOTALL)

        # Remove special characters and numbers, keeping only letters
        text = re.sub(r'[^a-z\s]', ' ', text)

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        return text