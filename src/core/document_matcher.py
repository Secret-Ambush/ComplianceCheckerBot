import logging
from typing import Dict, List, Optional, Tuple

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from src.models.document import Document, DocumentMatch, DocumentType

logger = logging.getLogger(__name__)


class DocumentMatcher:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize the document matcher.
        
        Args:
            model_name: Name of the sentence transformer model to use
        """
        self.model = SentenceTransformer(model_name)
    
    def find_matches(self, source_doc: Document, target_docs: List[Document], match_criteria: Dict) -> List[DocumentMatch]:
        """Find matching documents based on criteria.
        
        Args:
            source_doc: Source document to match
            target_docs: List of target documents to match against
            match_criteria: Dictionary of matching criteria
            
        Returns:
            List of document matches
        """
        matches = []
        
        for target_doc in target_docs:
            # Skip if document types don't match criteria
            if not self._check_document_types(source_doc, target_doc, match_criteria):
                continue
            
            # Calculate match confidence
            confidence, match_type, details = self._calculate_match_confidence(
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
    
    def _check_document_types(self, source_doc: Document, target_doc: Document, match_criteria: Dict) -> bool:
        """Check if document types match the criteria.
        
        Args:
            source_doc: Source document
            target_doc: Target document
            match_criteria: Matching criteria
            
        Returns:
            True if document types match, False otherwise
        """
        # Get required document types from criteria
        source_type = match_criteria.get("source_type")
        target_type = match_criteria.get("target_type")
        
        # Check if types match
        if source_type and source_doc.document_type != source_type:
            return False
        if target_type and target_doc.document_type != target_type:
            return False
        
        return True
    
    def _calculate_match_confidence(
        self, source_doc: Document, target_doc: Document, match_criteria: Dict
    ) -> Tuple[float, str, Dict]:
        """Calculate match confidence between documents.
        
        Args:
            source_doc: Source document
            target_doc: Target document
            match_criteria: Matching criteria
            
        Returns:
            Tuple of (confidence score, match type, match details)
        """
        # Initialize match details
        details = {}
        match_type = "unknown"
        
        # Check exact matches first
        if self._check_exact_matches(source_doc, target_doc, match_criteria, details):
            return 1.0, "exact", details
        
        # Check semantic matches
        if self._check_semantic_matches(source_doc, target_doc, match_criteria, details):
            return details.get("semantic_confidence", 0.0), "semantic", details
        
        # Check fuzzy matches
        if self._check_fuzzy_matches(source_doc, target_doc, match_criteria, details):
            return details.get("fuzzy_confidence", 0.0), "fuzzy", details
        
        return 0.0, "no_match", details
    
    def _check_exact_matches(
        self, source_doc: Document, target_doc: Document, match_criteria: Dict, details: Dict
    ) -> bool:
        """Check for exact matches between documents.
        
        Args:
            source_doc: Source document
            target_doc: Target document
            match_criteria: Matching criteria
            details: Dictionary to store match details
            
        Returns:
            True if exact match found, False otherwise
        """
        # Check document numbers
        if (source_doc.document_number and target_doc.document_number and
            source_doc.document_number == target_doc.document_number):
            details["exact_match"] = "document_number"
            return True
        
        # Check vendor IDs
        if (source_doc.vendor_id and target_doc.vendor_id and
            source_doc.vendor_id == target_doc.vendor_id):
            details["exact_match"] = "vendor_id"
            return True
        
        return False
    
    def _check_semantic_matches(
        self, source_doc: Document, target_doc: Document, match_criteria: Dict, details: Dict
    ) -> bool:
        """Check for semantic matches between documents.
        
        Args:
            source_doc: Source document
            target_doc: Target document
            match_criteria: Matching criteria
            details: Dictionary to store match details
            
        Returns:
            True if semantic match found, False otherwise
        """
        # Get text to compare
        source_text = self._get_comparison_text(source_doc)
        target_text = self._get_comparison_text(target_doc)
        
        if not source_text or not target_text:
            return False
        
        # Calculate semantic similarity
        source_embedding = self.model.encode([source_text])[0]
        target_embedding = self.model.encode([target_text])[0]
        
        similarity = cosine_similarity(
            source_embedding.reshape(1, -1),
            target_embedding.reshape(1, -1)
        )[0][0]
        
        details["semantic_confidence"] = float(similarity)
        return similarity >= match_criteria.get("min_semantic_similarity", 0.7)
    
    def _check_fuzzy_matches(
        self, source_doc: Document, target_doc: Document, match_criteria: Dict, details: Dict
    ) -> bool:
        """Check for fuzzy matches between documents.
        
        Args:
            source_doc: Source document
            target_doc: Target document
            match_criteria: Matching criteria
            details: Dictionary to store match details
            
        Returns:
            True if fuzzy match found, False otherwise
        """
        # TODO: Implement fuzzy matching logic
        # This could include:
        # - Fuzzy string matching on document numbers
        # - Date range matching
        # - Amount range matching
        # - Vendor name similarity
        return False
    
    def _get_comparison_text(self, doc: Document) -> Optional[str]:
        """Get text to use for comparison.
        
        Args:
            doc: Document to get text from
            
        Returns:
            Text to use for comparison
        """
        # Combine relevant fields for comparison
        text_parts = []
        
        if doc.document_number:
            text_parts.append(f"Document Number: {doc.document_number}")
        if doc.vendor_name:
            text_parts.append(f"Vendor: {doc.vendor_name}")
        if doc.vendor_id:
            text_parts.append(f"Vendor ID: {doc.vendor_id}")
        if doc.raw_text:
            text_parts.append(doc.raw_text)
        
        return " ".join(text_parts) if text_parts else None 