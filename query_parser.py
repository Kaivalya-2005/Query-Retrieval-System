import json
import re
from typing import Dict, Any
from transformers import pipeline

class QueryParser:
    def __init__(self):
        """Initialize the query parser with a local model"""
        # Use a small model that can run on CPU
        self.pipe = pipeline(
            "text2text-generation",
            model="google/flan-t5-small",  # Small model (~80MB) that can run on CPU
            device_map="auto"
        )
    
    def parse_query(self, query: str) -> Dict[str, Any]:
        """Parse a natural language query into structured fields"""
        prompt = f"""
        Extract structured information from this insurance query:
        "{query}"
        
        Extract age, gender, procedure, location, and policy duration.
        Format as JSON.
        """
        
        try:
            response = self.pipe(prompt, max_length=200, temperature=0.1)[0]['generated_text']
            
            # Try to extract JSON from the response
            json_match = re.search(r'(\{.*\})', response, re.DOTALL)
            if json_match:
                try:
                    structured_data = json.loads(json_match.group(0))
                    return structured_data
                except json.JSONDecodeError:
                    pass
        except Exception as e:
            print(f"Error with model generation: {e}")
            
        # Fallback to a rule-based parser
        return self._fallback_parse(query)
    
    def _fallback_parse(self, query: str) -> Dict[str, Any]:
        """Fallback method for parsing query using rules"""
        result = {}
        
        # Extract age
        age_match = re.search(r'(\d+)(?:[- ]?year[s]?[- ]?old|\s*M|\s*F)', query)
        if age_match:
            result["age"] = int(age_match.group(1))
        
        # Extract gender
        if "male" in query.lower() or " M " in query or query.endswith("M"):
            result["gender"] = "male"
        elif "female" in query.lower() or " F " in query or query.endswith("F"):
            result["gender"] = "female"
        
        # Basic procedure extraction
        procedures = ["surgery", "operation", "procedure", "treatment"]
        for proc in procedures:
            if proc in query.lower():
                # Get the words before the procedure type
                idx = query.lower().find(proc)
                start_idx = max(0, query.rfind(" ", 0, max(0, idx - 20)))
                result["procedure"] = query[start_idx:idx].strip() + " " + proc
                break
        
        # Extract location
        common_cities = ["pune", "mumbai", "delhi", "bangalore", "kolkata", "chennai"]
        for city in common_cities:
            if city.lower() in query.lower():
                result["location"] = city.title()
                break
        
        # Policy duration
        duration_match = re.search(r'(\d+)[ -]?(day|month|year|week)s?[ -]?(old )?policy', query.lower())
        if duration_match:
            result["policy_duration"] = {
                "value": int(duration_match.group(1)),
                "unit": duration_match.group(2) + "s"
            }
        
        return result