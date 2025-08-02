import os
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss  # For vector search

class VectorStore:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize the vector store with an embedding model"""
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.index = None
        self.texts = []
        self.metadata = []
        
    def add_documents(self, chunks: List[str], metadata: List[Dict[str, Any]] = None):
        """Add document chunks to the vector store"""
        if metadata is None:
            metadata = [{}] * len(chunks)
            
        # Generate embeddings for all chunks
        embeddings = self.model.encode(chunks)
        
        # Initialize FAISS index if not already done
        if self.index is None:
            self.index = faiss.IndexFlatL2(self.dimension)
            
        # Add to FAISS index
        faiss.normalize_L2(embeddings)
        self.index.add(embeddings)
        
        # Store the original texts and metadata
        self.texts.extend(chunks)
        self.metadata.extend(metadata)
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents given a query string"""
        if self.index is None or self.index.ntotal == 0:
            return []
            
        # Encode the query
        query_vector = self.model.encode([query])
        faiss.normalize_L2(query_vector)
        
        # Search the index
        distances, indices = self.index.search(query_vector, k)
        
        # Return results with scores and metadata
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1:  # -1 indicates no match
                results.append({
                    "content": self.texts[idx],
                    "score": float(1 - distances[0][i]),  # Convert to similarity score
                    "metadata": self.metadata[idx]
                })
                
        return results
    
    def save(self, directory: str):
        """Save the vector store to disk"""
        os.makedirs(directory, exist_ok=True)
        
        # Save the FAISS index
        faiss.write_index(self.index, os.path.join(directory, "index.faiss"))
        
        # Save the texts and metadata
        import pickle
        with open(os.path.join(directory, "data.pkl"), "wb") as f:
            pickle.dump({"texts": self.texts, "metadata": self.metadata}, f)
    
    @classmethod
    def load(cls, directory: str, model_name: str = "all-MiniLM-L6-v2"):
        """Load a vector store from disk"""
        store = cls(model_name)
        
        # Load the FAISS index
        store.index = faiss.read_index(os.path.join(directory, "index.faiss"))
        
        # Load the texts and metadata
        import pickle
        with open(os.path.join(directory, "data.pkl"), "rb") as f:
            data = pickle.load(f)
            store.texts = data["texts"]
            store.metadata = data["metadata"]
            
        return store