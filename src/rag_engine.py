"""
RAG Engine for Digital Twin Knowledge Base
Handles PDF loading, embeddings, and vector retrieval using ChromaDB
"""

import os
from typing import List, Dict
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma

# Load environment variables
load_dotenv()

class RAGEngine:
    """
    Manages the Retrieval-Augmented Generation knowledge base
    for pump troubleshooting documentation.
    """
    
    def __init__(
        self, 
        pdf_path: str = "../data/grundfos-cr-pump-troubleshooting.pdf",
        persist_directory: str = "./chroma_db",
        collection_name: str = "pump_manual"
    ):
        """
        Initialize the RAG engine with PDF document and vector store.
        
        Args:
            pdf_path: Path to the pump manual PDF
            persist_directory: Directory for ChromaDB persistence
            collection_name: Name of the ChromaDB collection
        """
        self.pdf_path = pdf_path
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Verify API key
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables!")
        
        # Initialize embeddings model
        print("🔧 Initializing Google Generative AI Embeddings...")
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=api_key
        )
        
        # Load or create vector store
        self.vector_store = self._initialize_vector_store()
        print("✅ RAG Engine initialized successfully!")
    
    def _load_and_split_pdf(self) -> List:
        """
        Load PDF and split into chunks with overlap.
        
        Returns:
            List of document chunks
        """
        print(f"📄 Loading PDF from: {self.pdf_path}")
        
        if not os.path.exists(self.pdf_path):
            raise FileNotFoundError(
                f"PDF not found at {self.pdf_path}. "
                "Please ensure the manual is in the data/ folder."
            )
        
        # Load PDF
        loader = PyPDFLoader(self.pdf_path)
        documents = loader.load()
        print(f"✅ Loaded {len(documents)} pages from PDF")
        
        # Split text into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        chunks = text_splitter.split_documents(documents)
        print(f"✅ Split into {len(chunks)} chunks (chunk_size=1000, overlap=200)")
        
        return chunks
    
    def _initialize_vector_store(self):
        """
        Initialize or load existing ChromaDB vector store.
        
        Returns:
            Chroma vector store instance
        """
        # Check if vector store already exists
        if os.path.exists(self.persist_directory):
            print(f"📦 Loading existing vector store from: {self.persist_directory}")
            vector_store = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )
            print(f"✅ Loaded vector store with {vector_store._collection.count()} documents")
            return vector_store
        
        # Create new vector store
        print("🆕 Creating new vector store...")
        chunks = self._load_and_split_pdf()
        
        print("🔮 Generating embeddings and storing in ChromaDB...")
        vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            collection_name=self.collection_name,
            persist_directory=self.persist_directory
        )
        
        print(f"✅ Vector store created with {len(chunks)} documents")
        return vector_store
    
    def query_knowledge_base(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        Retrieve relevant chunks from the knowledge base.
        
        Args:
            query: Search query (e.g., "motor overheating causes")
            top_k: Number of top results to return (default: 3)
        
        Returns:
            List of dictionaries containing:
                - content: The text chunk
                - metadata: Page number and source
                - score: Relevance score
        """
        print(f"🔍 Querying knowledge base: '{query[:50]}...'")
        
        # Perform similarity search with scores
        results = self.vector_store.similarity_search_with_score(
            query=query,
            k=top_k
        )
        
        # Format results
        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                "content": doc.page_content,
                "page": doc.metadata.get("page", "Unknown"),
                "source": doc.metadata.get("source", "Unknown"),
                "score": float(score)
            })
        
        print(f"✅ Retrieved {len(formatted_results)} relevant chunks")
        return formatted_results
    
    def get_context_for_prompt(self, query: str, top_k: int = 3) -> str:
        """
        Get formatted context string for LLM prompt.
        
        Args:
            query: Search query
            top_k: Number of chunks to retrieve
        
        Returns:
            Formatted context string with page references
        """
        results = self.query_knowledge_base(query, top_k)
        
        if not results:
            return "No relevant documentation found."
        
        context_parts = []
        for i, result in enumerate(results, 1):
            page = result['page']
            content = result['content']
            context_parts.append(f"[Reference {i} - Page {page}]\n{content}")
        
        return "\n\n".join(context_parts)
    
    def rebuild_index(self):
        """
        Force rebuild of the vector store (useful if PDF is updated).
        """
        print("🔄 Rebuilding vector store...")
        
        # Delete existing store
        if os.path.exists(self.persist_directory):
            import shutil
            shutil.rmtree(self.persist_directory)
            print(f"🗑️ Deleted existing store at {self.persist_directory}")
        
        # Reinitialize
        self.vector_store = self._initialize_vector_store()
        print("✅ Vector store rebuilt successfully!")


# Example usage and testing
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 TESTING RAG ENGINE")
    print("="*60 + "\n")
    
    try:
        # Initialize RAG engine
        rag = RAGEngine()
        
        # Test queries
        test_queries = [
            "What causes motor winding failure?",
            "How to check voltage imbalance?",
            "Symptoms of cavitation in pump"
        ]
        
        print("\n" + "-"*60)
        print("📋 RUNNING TEST QUERIES")
        print("-"*60 + "\n")
        
        for query in test_queries:
            print(f"\n🔍 Query: {query}")
            results = rag.query_knowledge_base(query, top_k=2)
            
            for i, result in enumerate(results, 1):
                print(f"\n  Result {i} (Page {result['page']}, Score: {result['score']:.3f}):")
                print(f"  {result['content'][:150]}...")
        
        print("\n" + "="*60)
        print("✅ RAG ENGINE TEST COMPLETE!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}\n")
        raise
