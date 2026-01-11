import pickle
import logging
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.email import Email
from app.models.embedding import Embedding
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class ClusteringService:
    """
    Service for similarity search and topic clustering using embeddings.
    """
    
    def __init__(self, embedding_service: Optional[EmbeddingService] = None):
        self.embedding_service = embedding_service or EmbeddingService()
    
    def find_similar_emails(
        self, 
        db: Session, 
        email_id: int, 
        threshold: float = 0.7, 
        limit: int = 10
    ) -> List[Tuple[Email, float]]:
        """
        Find emails similar to the given email.
        Returns list of (Email, similarity_score) tuples.
        """
        # Get embedding for target email
        target_embedding = db.query(Embedding).filter(
            Embedding.email_id == email_id
        ).first()
        
        if not target_embedding:
            logger.warning(f"No embedding found for email {email_id}")
            return []
        
        target_vector = self.embedding_service.get_vector(target_embedding)
        
        # Get all other email embeddings
        all_embeddings = db.query(Embedding).filter(
            Embedding.email_id.isnot(None),
            Embedding.email_id != email_id
        ).all()
        
        # Compute similarities
        similar = []
        for emb in all_embeddings:
            vector = self.embedding_service.get_vector(emb)
            similarity = self.embedding_service.compute_similarity(target_vector, vector)
            
            if similarity >= threshold:
                email = db.query(Email).filter(Email.id == emb.email_id).first()
                if email:
                    similar.append((email, similarity))
        
        # Sort by similarity descending
        similar.sort(key=lambda x: x[1], reverse=True)
        
        return similar[:limit]
    
    def cluster_emails(
        self, 
        db: Session, 
        email_ids: Optional[List[int]] = None,
        num_clusters: int = 5,
        min_cluster_size: int = 2
    ) -> Dict[int, List[int]]:
        """
        Cluster emails into topic groups using K-means style clustering.
        Returns dict mapping cluster_id -> list of email_ids.
        
        Uses a simple greedy clustering approach without numpy dependency.
        """
        # Get embeddings
        query = db.query(Embedding).filter(Embedding.email_id.isnot(None))
        if email_ids:
            query = query.filter(Embedding.email_id.in_(email_ids))
        
        embeddings = query.all()
        
        if len(embeddings) < min_cluster_size:
            logger.info("Not enough embeddings for clustering")
            return {}
        
        # Convert to vectors
        vectors = []
        email_map = []
        for emb in embeddings:
            vectors.append(self.embedding_service.get_vector(emb))
            email_map.append(emb.email_id)
        
        # Simple greedy clustering
        clusters = self._greedy_cluster(vectors, email_map, num_clusters, 0.6)
        
        # Filter small clusters
        result = {}
        cluster_id = 0
        for cluster_email_ids in clusters:
            if len(cluster_email_ids) >= min_cluster_size:
                result[cluster_id] = cluster_email_ids
                cluster_id += 1
        
        logger.info(f"Created {len(result)} clusters from {len(embeddings)} emails")
        return result
    
    def _greedy_cluster(
        self, 
        vectors: List[List[float]], 
        email_ids: List[int],
        max_clusters: int,
        similarity_threshold: float
    ) -> List[List[int]]:
        """
        Simple greedy clustering: assign each item to most similar cluster
        or create new cluster if similarity is below threshold.
        """
        if not vectors:
            return []
        
        clusters = [[email_ids[0]]]
        centroids = [vectors[0]]
        
        for i in range(1, len(vectors)):
            vector = vectors[i]
            email_id = email_ids[i]
            
            # Find best cluster
            best_cluster = -1
            best_similarity = 0.0
            
            for j, centroid in enumerate(centroids):
                similarity = self.embedding_service.compute_similarity(vector, centroid)
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_cluster = j
            
            # Assign to cluster or create new
            if best_similarity >= similarity_threshold or len(clusters) >= max_clusters:
                if best_cluster >= 0:
                    clusters[best_cluster].append(email_id)
                    # Update centroid (simple average)
                    old = centroids[best_cluster]
                    n = len(clusters[best_cluster])
                    centroids[best_cluster] = [
                        (old[k] * (n - 1) + vector[k]) / n 
                        for k in range(len(vector))
                    ]
            else:
                # Create new cluster
                clusters.append([email_id])
                centroids.append(vector)
        
        return clusters
    
    def suggest_groups(
        self, 
        db: Session, 
        mailbox_id: Optional[int] = None,
        limit: int = 5
    ) -> List[Dict]:
        """
        Suggest email groups based on clustering.
        Returns list of group suggestions with topic summary.
        """
        # Get recent emails with embeddings
        query = db.query(Email).join(
            Embedding, Email.id == Embedding.email_id
        )
        
        if mailbox_id:
            query = query.filter(Email.mailbox_id == mailbox_id)
        
        emails = query.order_by(Email.received_at.desc()).limit(100).all()
        email_ids = [e.id for e in emails]
        
        if not email_ids:
            return []
        
        # Cluster emails
        clusters = self.cluster_emails(db, email_ids, num_clusters=limit)
        
        # Build group suggestions
        suggestions = []
        for cluster_id, cluster_email_ids in clusters.items():
            # Get sample emails for topic extraction
            cluster_emails = [e for e in emails if e.id in cluster_email_ids]
            
            # Simple topic extraction: most common words in subjects
            subjects = [e.subject or "" for e in cluster_emails[:5]]
            topic = self._extract_topic(subjects)
            
            suggestions.append({
                "cluster_id": cluster_id,
                "topic": topic,
                "email_count": len(cluster_email_ids),
                "email_ids": cluster_email_ids[:10],  # First 10 for preview
                "sample_subjects": subjects[:3]
            })
        
        return suggestions
    
    def _extract_topic(self, subjects: List[str]) -> str:
        """
        Extract topic from subject lines (simple word frequency).
        """
        if not subjects:
            return "Unknown Topic"
        
        # Count words
        word_counts = {}
        stopwords = {"re", "fwd", "the", "a", "an", "is", "are", "was", "were", "to", "from", "for", "of", "and", "or", "in", "on", "at"}
        
        for subject in subjects:
            words = subject.lower().split()
            for word in words:
                word = word.strip(".,!?:;")
                if len(word) > 2 and word not in stopwords:
                    word_counts[word] = word_counts.get(word, 0) + 1
        
        if not word_counts:
            return subjects[0][:30] if subjects else "Unknown Topic"
        
        # Get top 3 words
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        top_words = [w[0].capitalize() for w in sorted_words[:3]]
        
        return " ".join(top_words)
