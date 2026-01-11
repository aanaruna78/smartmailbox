import pickle
import hashlib
import logging
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.email import Email
from app.models.thread import Thread
from app.models.embedding import Embedding

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating and managing text embeddings.
    Uses a simple local embedding model (sentence-transformers) or external API.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
    
    def _load_model(self):
        """Lazy load the embedding model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
                logger.info(f"Loaded embedding model: {self.model_name}")
            except ImportError:
                logger.warning("sentence-transformers not installed, using mock embeddings")
                self._model = "mock"
        return self._model
    
    def _get_content_hash(self, text: str) -> str:
        """Generate a hash of the content for cache invalidation."""
        return hashlib.sha256(text.encode()).hexdigest()[:16]
    
    def generate_embedding(self, text: str) -> tuple[list, int]:
        """
        Generate embedding vector for text.
        Returns (vector, dimension).
        """
        model = self._load_model()
        
        if model == "mock":
            # Mock embedding for testing
            import random
            dimension = 384
            vector = [random.random() for _ in range(dimension)]
            return vector, dimension
        
        # Real embedding
        vector = model.encode(text).tolist()
        dimension = len(vector)
        return vector, dimension
    
    def embed_email(self, db: Session, email: Email) -> Embedding:
        """
        Generate and store embedding for an email.
        """
        # Combine subject and body for embedding
        text = f"{email.subject or ''}\n\n{email.body_text or ''}"
        content_hash = self._get_content_hash(text)
        
        # Check if embedding already exists with same hash
        existing = db.query(Embedding).filter(
            Embedding.email_id == email.id,
            Embedding.content_hash == content_hash
        ).first()
        
        if existing:
            logger.info(f"Embedding already exists for email {email.id}")
            return existing
        
        # Generate new embedding
        vector, dimension = self.generate_embedding(text)
        
        # Delete old embeddings for this email
        db.query(Embedding).filter(Embedding.email_id == email.id).delete()
        
        # Create new embedding
        embedding = Embedding(
            email_id=email.id,
            model_name=self.model_name,
            dimension=dimension,
            vector=pickle.dumps(vector),
            content_hash=content_hash
        )
        db.add(embedding)
        db.commit()
        
        logger.info(f"Created embedding for email {email.id} (dim={dimension})")
        return embedding
    
    def embed_thread(self, db: Session, thread: Thread) -> Embedding:
        """
        Generate and store embedding for a thread (combined emails).
        """
        # Combine all email content in thread
        texts = []
        for email in thread.emails:
            texts.append(f"{email.subject or ''}: {email.body_text or ''}")
        
        combined_text = "\n\n---\n\n".join(texts)
        content_hash = self._get_content_hash(combined_text)
        
        # Check if embedding already exists
        existing = db.query(Embedding).filter(
            Embedding.thread_id == thread.id,
            Embedding.content_hash == content_hash
        ).first()
        
        if existing:
            logger.info(f"Embedding already exists for thread {thread.id}")
            return existing
        
        # Generate new embedding
        vector, dimension = self.generate_embedding(combined_text)
        
        # Delete old embeddings
        db.query(Embedding).filter(Embedding.thread_id == thread.id).delete()
        
        # Create new embedding
        embedding = Embedding(
            thread_id=thread.id,
            model_name=self.model_name,
            dimension=dimension,
            vector=pickle.dumps(vector),
            content_hash=content_hash
        )
        db.add(embedding)
        db.commit()
        
        logger.info(f"Created embedding for thread {thread.id} (dim={dimension})")
        return embedding
    
    def get_vector(self, embedding: Embedding) -> List[float]:
        """Deserialize the embedding vector."""
        return pickle.loads(embedding.vector)
    
    def compute_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        import math
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
