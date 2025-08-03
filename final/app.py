import os
from langchain.vectorstores import Pinecone
from langchain.embeddings import HuggingFaceBgeEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader, UnstructuredEmailLoader
from langchain.chains import RetrievalQA
from langchain_groq import ChatGroq
import pinecone
from dotenv import load_dotenv

load_dotenv()

# Initialize embeddings model with BGEM3
model_name = "BAAI/bge-large-en-v1.5"  # BGEM3 model
model_kwargs = {'device': 'cuda'}  # Use GPU if available
encode_kwargs = {'normalize_embeddings': True}

embedding = HuggingFaceBgeEmbeddings(
    model_name=model_name,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs
)

# Initialize Pinecone
pinecone.init(
    api_key=oos.getenv("PINECONE_API_KEY"),
    region="us-east-1"  # Change to your region
)

index_name = "document-retrieval"
# Create index if it doesn't exist
if index_name not in pinecone.list_indexes():
    pinecone.create_index(
        name=index_name,
        dimension=1024,  # BGEM3 embedding dimension
        metric="cosine"
    )

# Connect to the index
index = pinecone.Index(index_name)

# Create vector store
vectorstore = Pinecone(
    index, embedding.embed_query, "text"
)

# Document processing function
def process_document(file_path, metadata=None):
    # Determine loader based on file extension
    if file_path.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
    elif file_path.endswith(".docx"):
        loader = Docx2txtLoader(file_path)
    elif file_path.endswith(".txt"):
        loader = TextLoader(file_path)
    elif file_path.endswith(".eml"):
        loader = UnstructuredEmailLoader(file_path)
    else:
        raise ValueError("Unsupported file type")
    
    # Load documents
    documents = loader.load()
    
    # Add metadata if provided
    if metadata:
        for doc in documents:
            doc.metadata.update(metadata)
    
    # Split documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = text_splitter.split_documents(documents)
    
    # Add to vectorstore
    vectorstore.add_documents(chunks)
    
    return len(chunks)

# Query processing function
def process_query(query_text):
    # Create retrieval chain
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    
    # Initialize LLM with ChatGroq using llama-3.3-70b-versatile model
    llm = ChatGroq(
        model_name="llama-3.3-70b-versatile",
        temperature=0,
        groq_api_key=os.getenv("GROQ_API_KEY")
    )
    
    # Create QA chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever
    )
    
    # Process query
    result = qa_chain.run(query_text)
    
    return result