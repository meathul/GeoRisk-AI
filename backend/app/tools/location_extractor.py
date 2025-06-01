class LocationExtractor:
    def __init__(self, model):
        self.model = model

    def extract_location(self, text: str) -> str:
        prompt = (
            "Extract the location from this query. "
            "If no specific location is mentioned, respond with 'New York, NY'.\n\n"
            f"Query: {text}\n\nLocation:"
        )
        response = self.model.generate_text(prompt).strip()
        return response or "New York, NY"
