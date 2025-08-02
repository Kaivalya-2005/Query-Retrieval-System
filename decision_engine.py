from typing import Dict, Any, List
import re
import json
from transformers import pipeline

class DecisionEngine:
    def __init__(self):
        """Initialize the decision engine with local model"""
        # Use a small model that can run on CPU
        self.pipe = pipeline(
            "text2text-generation",
            model="google/flan-t5-small",  # Small model (~80MB) that can run on CPU
            device_map="auto"
        )
    
    def make_decision(self, structured_query: Dict[str, Any], relevant_clauses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Make a decision based on structured query and relevant clauses"""
        # Format the query and clauses for the prompt
        query_str = ", ".join([f"{k}: {v}" for k, v in structured_query.items() if isinstance(v, (str, int, float))])
        
        # Join relevant clauses
        clauses_text = "\n".join([f"Clause {i+1}: {c['content'][:200]}" for i, c in enumerate(relevant_clauses[:3])])
        
        prompt = f"""
        Given these insurance claim details:
        {query_str}
        
        And these policy clauses:
        {clauses_text}
        
        Determine if the claim is approved or rejected and explain why.
        """
        
        try:
            # Generate a decision
            response = self.pipe(prompt, max_length=200, temperature=0.1)[0]['generated_text']
            
            # Try to parse the decision from the text
            if "approved" in response.lower():
                decision = "approved"
            elif "rejected" in response.lower():
                decision = "rejected"
            else:
                decision = "undetermined"
                
            # Extract any numbers that might be amounts
            amount_match = re.search(r'(\d+,?\d*)', response)
            amount = float(amount_match.group(0).replace(',', '')) if amount_match else None
            
            # Use the response as justification
            justification = response.strip()
            
            # Extract clause references
            clause_refs = []
            for i, clause in enumerate(relevant_clauses[:3]):
                if f"Clause {i+1}" in response or f"clause {i+1}" in response.lower():
                    clause_refs.append(f"Clause {i+1}")
            
            return {
                "decision": decision,
                "amount": amount,
                "justification": justification,
                "clause_references": clause_refs
            }
            
        except Exception as e:
            print(f"Error in decision engine: {e}")
            return {
                "decision": "undetermined",
                "amount": None,
                "justification": "Unable to determine decision due to processing error.",
                "clause_references": []
            }