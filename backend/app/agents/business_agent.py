from typing import List

class BusinessRiskAgent:
    def __init__(self, business_retriever, model):
        self.retriever = business_retriever
        self.model = model

    def analyze_business_impact(self, location: str, climate_analysis: str, user_query: str) -> str:
        business_queries = [
            f"supply chain risk climate business continuity {location}",
            f"operational resilience climate adaptation {location}",
            f"financial impact climate change business {location}",
            f"risk management climate hazards enterprise {location}"
        ]
        all_docs = []
        if self.retriever:
            for q in business_queries:
                docs = self.retriever.invoke(q)
                all_docs.extend(docs[:2])

        context = self._build_business_context(all_docs)
        prompt = self._build_risk_prompt(location, climate_analysis, user_query, context)
        enhanced_params = {
            "decoding_method": "greedy",
            "max_new_tokens": 2500,
            "temperature": 0.8,
            "stop_sequences": ["\n\n\n"]
        }
        return self.model.generate_text(prompt=prompt, params=enhanced_params).strip()

    def _build_business_context(self, docs: List) -> str:
        if not docs:
            return "No specific business documents found; use general best practices for climate risk."
        parts = ["--- BUSINESS RISK DOCUMENTS ---"]
        for i, doc in enumerate(docs[:8], 1):
            source = doc.metadata.get("source", f"Source {i}")
            content = doc.page_content[:600] + "..."
            parts.append(f"\nDocument {i}: {source}\nContent: {content}")
        return "\n".join(parts)

    def _build_risk_prompt(self, location: str, climate_analysis: str, user_query: str, context: str) -> str:
        return f"""You are a Senior Business Continuity Consultant.

            LOCATION: {location}
            USER QUESTION: {user_query}

            CLIMATE ANALYSIS:
            {climate_analysis}

            BUSINESS CONTEXT:
            {context}

            Provide a detailed operational impact analysis, financial impact assessment, strategic mitigation framework 
            (immediate to long-term), implementation roadmap, strategic recommendations, and plan evaluation. 
            Include specific examples, timelines, and financial estimates.

            BUSINESS IMPACT ANALYSIS:"""
