from typing import Dict, List

class ClimateAgent:
    def __init__(self, climate_retriever, serper_service, model):
        self.retriever = climate_retriever
        self.serper = serper_service
        self.model = model

    def analyze_climate_risks(self, location: str, user_query: str) -> Dict:
        search_results = {
            "weather": self.serper.search_climate_data(location, "weather"),
            "risks": self.serper.search_climate_data(location, "risks"),
            "news": self.serper.search_climate_data(location, "news"),
            "projections": self.serper.search_climate_data(location, "projections")
        }

        climate_queries = [
            f"climate change impacts {location} temperature precipitation extreme weather",
            f"sea level rise flooding {location} coastal risks",
            f"drought water scarcity {location} agriculture",
            f"extreme heat heatwave {location} infrastructure"
        ]
        all_docs = []
        if self.retriever:
            for q in climate_queries:
                docs = self.retriever.invoke(q)
                all_docs.extend(docs[:2])

        context = self._build_context(search_results, all_docs)

        prompt = self._build_analysis_prompt(location, user_query, context)
        enhanced_params = {
            "decoding_method": "greedy",
            "max_new_tokens": 2000,
            "temperature": 0.8,
            "stop_sequences": ["\n\n\n"]
        }
        analysis = self.model.generate_text(prompt=prompt, params=enhanced_params).strip()

        return {
            "analysis": analysis,
            "location": location,
            "search_data": search_results,
            "sources_used": len(all_docs),
            "search_queries_used": len(climate_queries)
        }

    def _build_context(self, search_results: Dict, local_docs: List) -> str:
        parts = []
        for stype, results in search_results.items():
            if results.get("success"):
                parts.append(f"\n--- {stype.upper()} ---")
                for item in results.get("results", [])[:5]:
                    title = item.get("title", "")
                    snippet = item.get("snippet", "")
                    link = item.get("link", "")
                    if title and snippet:
                        parts.append(f"• {title}\n  Summary: {snippet}\n  Source: {link}\n")
                news_items = results.get("news", [])
                if news_items:
                    parts.append(f"--- {stype.upper()} NEWS ---")
                    for news in news_items[:3]:
                        title = news.get("title", "")
                        snippet = news.get("snippet", "")
                        if title and snippet:
                            parts.append(f"• {title}: {snippet}")
        if local_docs:
            parts.append("\n--- LOCAL CLIMATE DATABASE ---")
            for doc in local_docs[:8]:
                source = doc.metadata.get("source", "Unknown Source")
                content = doc.page_content[:500] + "..."
                parts.append(f"\nDocument: {source}\nContent: {content}")
        return "\n".join(parts)

    def _build_analysis_prompt(self, location: str, user_query: str, context: str) -> str:
        return f"""You are a Senior Climate Risk Analyst with 15+ years of experience.

            LOCATION: {location}
            USER QUESTION: {user_query}

            DATA SOURCES:
            {context}

            Provide a detailed analysis covering current conditions, historical trends, future projections, risk assessment, economic impacts, data confidence, and limitations.
            Use at least 4-5 points in each section and include specific examples and numbers.

            CLIMATE ANALYSIS:"""
