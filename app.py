import os
import tempfile
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import json

from document_processor import DocumentProcessor
from vector_store import VectorStore
from query_parser import QueryParser
from decision_engine import DecisionEngine

app = FastAPI(title="LLM Document Processing System")

# Add this new model near the top with your other imports and models
class QueryRequest(BaseModel):
    query: str
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
document_processor = DocumentProcessor()
vector_store = VectorStore()
query_parser = QueryParser()
decision_engine = DecisionEngine()

# Model for response
class ProcessResponse(BaseModel):
    decision: str
    amount: Optional[float] = None
    justification: str
    clause_references: List[str]
    structured_query: Dict[str, Any]
    relevant_clauses: List[Dict[str, Any]]

@app.post("/upload_document")
async def upload_document(file: UploadFile = File(...), metadata: str = Form("{}")):
    """Upload and process a document"""
    try:
        # Parse metadata
        meta_dict = json.loads(metadata)
        
        # Save the uploaded file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            temp_file.write(await file.read())
            temp_file_path = temp_file.name
        
        try:
            # Process the document
            chunks = document_processor.process_document(temp_file_path)
            
            # Create metadata for each chunk
            chunk_metadata = []
            for i, chunk in enumerate(chunks):
                chunk_meta = meta_dict.copy()
                chunk_meta["document_name"] = file.filename
                chunk_meta["chunk_id"] = i
                chunk_metadata.append(chunk_meta)
            
            # Add to vector store
            vector_store.add_documents(chunks, chunk_metadata)
            
            return {"message": f"Document processed successfully with {len(chunks)} chunks"}
        finally:
            # Clean up the temporary file
            os.unlink(temp_file_path)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@app.post("/process_query", response_model=ProcessResponse)
async def process_query(query_request: QueryRequest):
    """Process a natural language query and return a decision"""
    try:
        query = query_request.query
        print(f"Processing query: {query}")  # Debug log
        
        # Parse the query
        structured_query = query_parser.parse_query(query)
        
        # Build a search query from the structured data
        search_terms = []
        for k, v in structured_query.items():
            if v and k != "policy_duration":
                if isinstance(v, (str, int, float)):
                    search_terms.append(f"{k}: {v}")
                
        search_query = " ".join(search_terms)
        
        if "policy_duration" in structured_query and isinstance(structured_query["policy_duration"], dict):
            pd = structured_query["policy_duration"]
            if "value" in pd and "unit" in pd:
                search_query += f" policy duration: {pd['value']} {pd['unit']}"
        
        # Search for relevant clauses
        relevant_clauses = vector_store.search(search_query, k=5)
        
        # Make a decision
        decision = decision_engine.make_decision(structured_query, relevant_clauses)
        
        # Add structured query and relevant clauses to response
        decision["structured_query"] = structured_query
        decision["relevant_clauses"] = relevant_clauses
        
        return decision
        
    except Exception as e:
        import traceback
        print(f"Error processing query: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get("/status")
async def get_status():
    """Get the status of the system"""
    return {
        "status": "running",
        "documents_processed": 0 if vector_store.index is None else vector_store.index.ntotal,
    }