import logging
from typing import Dict, List, Optional, Tuple, Union
import torch
from transformers import AutoTokenizer, AutoModel
from sentence_transformers import SentenceTransformer
import numpy as np
from datetime import datetime

from src.models.document import Document
from src.models.validation import ValidationResult, ValidationIssue

logger = logging.getLogger(__name__)

class EnhancedAIEngine:
    def __init__(
        self,
        transformer_model_name: str = "microsoft/mdeberta-v3-base",
        sentence_transformer_name: str = "all-MiniLM-L6-v2"
    ):
        """Initialize the enhanced AI engine.
        
        Args:
            transformer_model_name: Name of the transformer model for document understanding
            sentence_transformer_name: Name of the sentence transformer model for semantic matching
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")
        
        # Initialize models
        self.tokenizer = AutoTokenizer.from_pretrained(transformer_model_name)
        self.transformer = AutoModel.from_pretrained(transformer_model_name).to(self.device)
        self.sentence_transformer = SentenceTransformer(sentence_transformer_name)
        
        # Set models to evaluation mode
        self.transformer.eval()
    
    def analyze_document(self, document: Document) -> Dict:
        """Analyze document content using advanced AI techniques.
        
        Args:
            document: Document to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        # Extract text content
        text = document.get_text_content()
        
        # Perform various analyses
        entities = self._extract_entities(text)
        semantic_context = self._analyze_semantic_context(text)
        document_type = self._classify_document_type(text)
        
        # Calculate confidence scores
        confidence_scores = {
            "entity_extraction": self._calculate_confidence(entities),
            "semantic_analysis": self._calculate_confidence(semantic_context),
            "document_classification": self._calculate_confidence(document_type)
        }
        
        return {
            "entities": entities,
            "semantic_context": semantic_context,
            "document_type": document_type,
            "confidence_scores": confidence_scores,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def optimize_rules(self, validation_results: List[ValidationResult]) -> Dict:
        """Analyze and optimize validation rules based on historical results.
        
        Args:
            validation_results: List of validation results
            
        Returns:
            Dictionary containing optimization suggestions
        """
        # Analyze rule effectiveness
        effectiveness = self._analyze_rule_effectiveness(validation_results)
        
        # Generate optimization suggestions
        suggestions = self._generate_optimization_suggestions(effectiveness)
        
        return {
            "rule_effectiveness": effectiveness,
            "optimization_suggestions": suggestions,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities from text using transformer model.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary mapping entity types to lists of entities
        """
        # Tokenize text
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512
        ).to(self.device)
        
        # Get model predictions
        with torch.no_grad():
            outputs = self.transformer(**inputs)
        
        # Process outputs to extract entities
        # This is a simplified version - in practice, you'd want to use a proper NER model
        entities = {
            "dates": [],
            "amounts": [],
            "parties": [],
            "references": []
        }
        
        # Add entity extraction logic here
        # For now, return empty lists
        
        return entities
    
    def _analyze_semantic_context(self, text: str) -> Dict:
        """Analyze semantic context of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary containing semantic analysis results
        """
        # Get sentence embeddings
        sentences = text.split(". ")
        embeddings = self.sentence_transformer.encode(sentences)
        
        # Calculate semantic similarity matrix
        similarity_matrix = np.inner(embeddings, embeddings)
        
        # Extract key topics and themes
        # This is a simplified version - in practice, you'd want to use topic modeling
        topics = {
            "main_themes": [],
            "key_concepts": [],
            "semantic_clusters": []
        }
        
        return {
            "topics": topics,
            "similarity_matrix": similarity_matrix.tolist()
        }
    
    def _classify_document_type(self, text: str) -> Tuple[str, float]:
        """Classify document type using zero-shot classification.
        
        Args:
            text: Text to classify
            
        Returns:
            Tuple of (document_type, confidence_score)
        """
        # Define possible document types
        document_types = [
            "invoice",
            "purchase_order",
            "contract",
            "receipt",
            "statement"
        ]
        
        # Get text embedding
        text_embedding = self.sentence_transformer.encode(text)
        
        # Get document type embeddings
        type_embeddings = self.sentence_transformer.encode(document_types)
        
        # Calculate similarities
        similarities = np.inner(text_embedding, type_embeddings)
        
        # Get best match
        best_idx = np.argmax(similarities)
        confidence = float(similarities[best_idx])
        
        return document_types[best_idx], confidence
    
    def _calculate_confidence(self, result: Union[Dict, List, str]) -> float:
        """Calculate confidence score for an analysis result.
        
        Args:
            result: Analysis result
            
        Returns:
            Confidence score between 0 and 1
        """
        # This is a simplified version - in practice, you'd want to use
        # model-specific confidence scores or ensemble methods
        if isinstance(result, dict):
            # For entity extraction results
            return 0.8 if result.get("entities") else 0.5
        elif isinstance(result, list):
            # For list results
            return 0.7 if result else 0.3
        elif isinstance(result, str):
            # For classification results
            return 0.9 if result else 0.4
        else:
            return 0.5
    
    def _analyze_rule_effectiveness(self, validation_results: List[ValidationResult]) -> Dict:
        """Analyze effectiveness of validation rules.
        
        Args:
            validation_results: List of validation results
            
        Returns:
            Dictionary containing rule effectiveness metrics
        """
        effectiveness = {}
        
        for result in validation_results:
            rule_id = result.document_id
            
            if rule_id not in effectiveness:
                effectiveness[rule_id] = {
                    "total_runs": 0,
                    "pass_count": 0,
                    "fail_count": 0,
                    "warning_count": 0,
                    "error_count": 0,
                    "avg_execution_time": 0.0
                }
            
            metrics = effectiveness[rule_id]
            metrics["total_runs"] += 1
            
            if result.status == "PASS":
                metrics["pass_count"] += 1
            elif result.status == "FAIL":
                metrics["fail_count"] += 1
            elif result.status == "WARNING":
                metrics["warning_count"] += 1
            elif result.status == "ERROR":
                metrics["error_count"] += 1
            
            # Update average execution time
            metrics["avg_execution_time"] = (
                (metrics["avg_execution_time"] * (metrics["total_runs"] - 1) +
                 result.execution_time) / metrics["total_runs"]
            )
        
        return effectiveness
    
    def _generate_optimization_suggestions(self, effectiveness: Dict) -> List[Dict]:
        """Generate optimization suggestions based on rule effectiveness.
        
        Args:
            effectiveness: Dictionary containing rule effectiveness metrics
            
        Returns:
            List of optimization suggestions
        """
        suggestions = []
        
        for rule_id, metrics in effectiveness.items():
            # Calculate pass rate
            pass_rate = metrics["pass_count"] / metrics["total_runs"]
            
            # Generate suggestions based on metrics
            if pass_rate < 0.5:
                suggestions.append({
                    "rule_id": rule_id,
                    "type": "high_failure_rate",
                    "message": f"Rule has high failure rate ({pass_rate:.2%} pass rate)",
                    "suggestion": "Consider relaxing validation criteria or adding more context"
                })
            
            if metrics["avg_execution_time"] > 1.0:
                suggestions.append({
                    "rule_id": rule_id,
                    "type": "performance",
                    "message": f"Rule has high execution time ({metrics['avg_execution_time']:.2f}s)",
                    "suggestion": "Consider optimizing rule implementation or using caching"
                })
            
            if metrics["error_count"] > 0:
                suggestions.append({
                    "rule_id": rule_id,
                    "type": "reliability",
                    "message": f"Rule has {metrics['error_count']} errors",
                    "suggestion": "Review error handling and add more robust validation"
                })
        
        return suggestions 