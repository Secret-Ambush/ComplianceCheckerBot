import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
from datetime import datetime
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import AutoTokenizer, AutoModel
import torch
from fuzzywuzzy import fuzz
from dateutil.parser import parse as parse_date

from src.models.document import Document, DocumentMatch, DocumentType

logger = logging.getLogger(__name__)

class EnhancedDocumentMatcher:
    def __init__(
        self,
        semantic_model_name: str = "all-MiniLM-L6-v2",
        advanced_model_name: str = "microsoft/deberta-v3-base"
    ):
        """Initialize the enhanced document matcher.
        
        Args:
            semantic_model_name: Name of the sentence transformer model for basic semantic matching
            advanced_model_name: Name of the advanced transformer model for complex matching
        """
        self.semantic_model = SentenceTransformer(semantic_model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(advanced_model_name)
        self.advanced_model = AutoModel.from_pretrained(advanced_model_name)
        
    def find_matches(
        self,
        source_doc: Document,
        target_docs: List[Document],
        match_criteria: Dict
    ) -> List[DocumentMatch]:
        """Find matching documents using enhanced matching capabilities.
        
        Args:
            source_doc: Source document to match
            target_docs: List of target documents to match against
            match_criteria: Dictionary of matching criteria
            
        Returns:
            List of document matches with confidence scores and match types
        """
        matches = []
        
        for target_doc in target_docs:
            # Skip if document types don't match criteria
            if not self._check_document_types(source_doc, target_doc, match_criteria):
                continue
            
            # Calculate match confidence using multiple strategies
            confidence, match_type, details = self._calculate_enhanced_match_confidence(
                source_doc, target_doc, match_criteria
            )
            
            # Create match if confidence is high enough
            if confidence >= match_criteria.get("min_confidence", 0.7):
                match = DocumentMatch(
                    source_document=source_doc.id,
                    target_document=target_doc.id,
                    match_confidence=confidence,
                    match_type=match_type,
                    match_criteria=details
                )
                matches.append(match)
        
        return matches
    
    def _calculate_enhanced_match_confidence(
        self,
        source_doc: Document,
        target_doc: Document,
        match_criteria: Dict
    ) -> Tuple[float, str, Dict]:
        """Calculate match confidence using multiple strategies.
        
        Args:
            source_doc: Source document
            target_doc: Target document
            match_criteria: Matching criteria
            
        Returns:
            Tuple of (confidence score, match type, match details)
        """
        details = {}
        match_type = "unknown"
        
        # 1. Check exact matches
        if self._check_exact_matches(source_doc, target_doc, match_criteria, details):
            return 1.0, "exact", details
        
        # 2. Check advanced semantic matches
        semantic_confidence = self._check_advanced_semantic_matches(
            source_doc, target_doc, match_criteria, details
        )
        
        # 3. Check contextual matches
        contextual_confidence = self._check_contextual_matches(
            source_doc, target_doc, match_criteria, details
        )
        
        # 4. Check fuzzy matches
        fuzzy_confidence = self._check_enhanced_fuzzy_matches(
            source_doc, target_doc, match_criteria, details
        )
        
        # Combine confidences with weights
        weights = {
            "semantic": 0.4,
            "contextual": 0.3,
            "fuzzy": 0.3
        }
        
        final_confidence = (
            semantic_confidence * weights["semantic"] +
            contextual_confidence * weights["contextual"] +
            fuzzy_confidence * weights["fuzzy"]
        )
        
        # Determine match type based on highest confidence
        confidences = {
            "semantic": semantic_confidence,
            "contextual": contextual_confidence,
            "fuzzy": fuzzy_confidence
        }
        match_type = max(confidences.items(), key=lambda x: x[1])[0]
        
        details["final_confidence"] = final_confidence
        details["confidence_breakdown"] = confidences
        
        return final_confidence, match_type, details
    
    def _check_advanced_semantic_matches(
        self,
        source_doc: Document,
        target_doc: Document,
        match_criteria: Dict,
        details: Dict
    ) -> float:
        """Check for advanced semantic matches using transformer models.
        
        Args:
            source_doc: Source document
            target_doc: Target document
            match_criteria: Matching criteria
            details: Dictionary to store match details
            
        Returns:
            Semantic match confidence score
        """
        # Get text to compare
        source_text = self._get_comparison_text(source_doc)
        target_text = self._get_comparison_text(target_doc)
        
        if not source_text or not target_text:
            return 0.0
        
        # Calculate semantic similarity using advanced model
        source_tokens = self.tokenizer(
            source_text,
            return_tensors="pt",
            truncation=True,
            max_length=512
        )
        target_tokens = self.tokenizer(
            target_text,
            return_tensors="pt",
            truncation=True,
            max_length=512
        )
        
        with torch.no_grad():
            source_output = self.advanced_model(**source_tokens)
            target_output = self.advanced_model(**target_tokens)
            
            source_embedding = source_output.last_hidden_state.mean(dim=1)
            target_embedding = target_output.last_hidden_state.mean(dim=1)
            
            similarity = cosine_similarity(
                source_embedding.numpy(),
                target_embedding.numpy()
            )[0][0]
        
        details["semantic_confidence"] = float(similarity)
        return float(similarity)
    
    def _check_contextual_matches(
        self,
        source_doc: Document,
        target_doc: Document,
        match_criteria: Dict,
        details: Dict
    ) -> float:
        """Check for contextual matches considering document relationships.
        
        Args:
            source_doc: Source document
            target_doc: Target document
            match_criteria: Matching criteria
            details: Dictionary to store match details
            
        Returns:
            Contextual match confidence score
        """
        confidence = 0.0
        context_factors = []
        
        # Check date proximity
        if source_doc.date and target_doc.date:
            date_diff = abs((source_doc.date - target_doc.date).days)
            if date_diff <= 7:  # Within 7 days
                date_confidence = 1.0 - (date_diff / 7)
                context_factors.append(("date_proximity", date_confidence))
        
        # Check amount proximity
        if source_doc.total_amount and target_doc.total_amount:
            amount_diff = abs(source_doc.total_amount - target_doc.total_amount)
            if amount_diff <= source_doc.total_amount * 0.1:  # Within 10%
                amount_confidence = 1.0 - (amount_diff / (source_doc.total_amount * 0.1))
                context_factors.append(("amount_proximity", amount_confidence))
        
        # Check vendor name similarity
        if source_doc.vendor_name and target_doc.vendor_name:
            vendor_similarity = fuzz.ratio(
                source_doc.vendor_name.lower(),
                target_doc.vendor_name.lower()
            ) / 100.0
            context_factors.append(("vendor_similarity", vendor_similarity))
        
        if context_factors:
            confidence = sum(score for _, score in context_factors) / len(context_factors)
        
        details["contextual_factors"] = dict(context_factors)
        details["contextual_confidence"] = confidence
        
        return confidence
    
    def _check_enhanced_fuzzy_matches(
        self,
        source_doc: Document,
        target_doc: Document,
        match_criteria: Dict,
        details: Dict
    ) -> float:
        """Check for enhanced fuzzy matches using multiple strategies.
        
        Args:
            source_doc: Source document
            target_doc: Target document
            match_criteria: Matching criteria
            details: Dictionary to store match details
            
        Returns:
            Fuzzy match confidence score
        """
        fuzzy_factors = []
        
        # Check document number similarity
        if source_doc.document_number and target_doc.document_number:
            doc_num_similarity = fuzz.ratio(
                source_doc.document_number,
                target_doc.document_number
            ) / 100.0
            fuzzy_factors.append(("document_number", doc_num_similarity))
        
        # Check vendor ID similarity
        if source_doc.vendor_id and target_doc.vendor_id:
            vendor_id_similarity = fuzz.ratio(
                source_doc.vendor_id,
                target_doc.vendor_id
            ) / 100.0
            fuzzy_factors.append(("vendor_id", vendor_id_similarity))
        
        # Check raw text similarity
        if source_doc.raw_text and target_doc.raw_text:
            text_similarity = fuzz.token_sort_ratio(
                source_doc.raw_text,
                target_doc.raw_text
            ) / 100.0
            fuzzy_factors.append(("text_similarity", text_similarity))
        
        if fuzzy_factors:
            confidence = sum(score for _, score in fuzzy_factors) / len(fuzzy_factors)
        else:
            confidence = 0.0
        
        details["fuzzy_factors"] = dict(fuzzy_factors)
        details["fuzzy_confidence"] = confidence
        
        return confidence
    
    def _get_comparison_text(self, doc: Document) -> Optional[str]:
        """Get text to use for comparison.
        
        Args:
            doc: Document to get text from
            
        Returns:
            Text to use for comparison
        """
        text_parts = []
        
        if doc.document_number:
            text_parts.append(f"Document Number: {doc.document_number}")
        if doc.vendor_name:
            text_parts.append(f"Vendor: {doc.vendor_name}")
        if doc.vendor_id:
            text_parts.append(f"Vendor ID: {doc.vendor_id}")
        if doc.date:
            text_parts.append(f"Date: {doc.date.isoformat()}")
        if doc.total_amount:
            text_parts.append(f"Amount: {doc.total_amount} {doc.currency}")
        if doc.raw_text:
            text_parts.append(doc.raw_text)
        
        return " ".join(text_parts) if text_parts else None 