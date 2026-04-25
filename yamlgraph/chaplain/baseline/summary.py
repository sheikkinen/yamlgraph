"""Summary caching for deterministic baseline content."""

import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, Any
from unittest.mock import Mock


class SummaryCache:
    """Cache for summarized content with deterministic keys."""
    
    def __init__(self, cache_file: Path):
        """
        Initialize summary cache.
        
        Args:
            cache_file: Path to cache file
        """
        self.cache_file = Path(cache_file)
        self.cache_hit = False
        self._cache_data: Dict[str, Dict[str, Any]] = {}
        
        # Load existing cache if it exists
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    self._cache_data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._cache_data = {}
    
    def get_or_generate_summary(
        self, 
        source_content: str, 
        summary_prompt_version: str, 
        summary_model: str
    ) -> str:
        """
        Get cached summary or generate new one.
        
        Summary cache key: sha256(source_content + summary_prompt_version + summary_model)
        
        Args:
            source_content: Content to summarize
            summary_prompt_version: Version of summary prompt
            summary_model: Model used for summarization
            
        Returns:
            str: Summary text
        """
        # Compute cache key
        cache_key = self._compute_cache_key(source_content, summary_prompt_version, summary_model)
        
        # Check cache
        if cache_key in self._cache_data:
            self.cache_hit = True
            return self._cache_data[cache_key]["summary"]
        
        # Generate new summary (mock for testing)
        self.cache_hit = False
        summary = f"Summary of: {source_content[:50]}..."
        
        # Store in cache
        self._cache_data[cache_key] = {
            "summary": summary,
            "summary_model": summary_model,
            "summary_prompt_version": summary_prompt_version,
            "source_content_hash": hashlib.sha256(source_content.encode()).hexdigest()
        }
        
        # Write cache to disk
        self._write_cache()
        
        return summary
    
    def _compute_cache_key(self, source_content: str, summary_prompt_version: str, summary_model: str) -> str:
        """
        Compute deterministic cache key for summary.
        
        Args:
            source_content: Content being summarized
            summary_prompt_version: Version of summary prompt
            summary_model: Model used for summarization
            
        Returns:
            str: SHA256 hex digest cache key
        """
        key_input = f"{source_content}|{summary_prompt_version}|{summary_model}"
        return hashlib.sha256(key_input.encode('utf-8')).hexdigest()
    
    def _write_cache(self):
        """Write cache data to disk."""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_file, 'w') as f:
            json.dump(self._cache_data, f, indent=2)