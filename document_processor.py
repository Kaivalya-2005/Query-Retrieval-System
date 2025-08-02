import os
from typing import List, Dict, Any
import fitz  # PyMuPDF for PDF processing
import docx  # python-docx for Word documents
import email
import re
from email.parser import BytesParser
from email.policy import default

class DocumentProcessor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
    def process_document(self, file_path: str) -> List[str]:
        """Process document based on file extension and return chunks of text"""
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        if ext == '.pdf':
            return self._process_pdf(file_path)
        elif ext == '.docx':
            return self._process_docx(file_path)
        elif ext in ['.eml', '.msg']:
            return self._process_email(file_path)
        elif ext == '.txt':
            return self._process_text(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")
    
    def _process_pdf(self, file_path: str) -> List[str]:
        """Extract text from PDF and split into chunks"""
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return self._chunk_text(text)
    
    def _process_docx(self, file_path: str) -> List[str]:
        """Extract text from DOCX and split into chunks"""
        doc = docx.Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        return self._chunk_text(text)
    
    def _process_email(self, file_path: str) -> List[str]:
        """Extract text from email and split into chunks"""
        with open(file_path, 'rb') as fp:
            msg = BytesParser(policy=default).parse(fp)
        
        text = f"Subject: {msg['subject']}\n\n"
        
        # Get the email body
        if msg.is_multipart():
            for part in msg.iter_parts():
                if part.get_content_type() == "text/plain":
                    text += part.get_content()
        else:
            text += msg.get_content()
            
        return self._chunk_text(text)
    
    def _process_text(self, file_path: str) -> List[str]:
        """Process plain text file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        return self._chunk_text(text)
    
    def _chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks of approximately chunk_size characters"""
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            if end >= len(text):
                chunks.append(text[start:])
                break
                
            # Try to find a good breaking point (end of sentence or paragraph)
            chunk_end = self._find_break_point(text, end)
            chunks.append(text[start:chunk_end])
            
            # Move the start pointer with overlap
            start = chunk_end - self.chunk_overlap
            
        return chunks
    
    def _find_break_point(self, text: str, pos: int) -> int:
        """Find a good breaking point near the specified position"""
        # Look for paragraph break
        paragraph_match = text.find('\n\n', pos - 100, pos + 100)
        if paragraph_match != -1 and abs(paragraph_match - pos) < 100:
            return paragraph_match + 2
        
        # Look for sentence end
        for i in range(pos, min(pos + 100, len(text))):
            if text[i] in ['.', '!', '?'] and (i + 1 >= len(text) or text[i + 1].isspace()):
                return i + 1
                
        # Look for sentence end before pos
        for i in range(pos, max(pos - 100, 0), -1):
            if text[i] in ['.', '!', '?'] and (i + 1 >= len(text) or text[i + 1].isspace()):
                return i + 1
                
        # If no good break point found, just break at the position
        return pos