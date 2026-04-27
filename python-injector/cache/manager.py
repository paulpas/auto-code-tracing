#!/usr/bin/env python3
"""Enhanced cache management for telemetry-aware code injection."""

import hashlib
import json
import pathlib
import logging
from typing import Optional

log = logging.getLogger(__name__)

class CacheManager:
    def __init__(self, cache_dir: str = ".debug_cache"):
        self.cache_dir = pathlib.Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.telemetry_version = "v2.0"  # Increment when telemetry changes
    
    def get_cache_key(self, src_path: pathlib.Path, service_name: str = "") -> str:
        """Generate cache key including service name and telemetry version."""
        content = src_path.read_text(encoding="utf-8")
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        cache_key = f"{service_name}_{src_path.name}_{content_hash}_{self.telemetry_version}"
        return cache_key
    
    def get_cached_content(self, src_path: pathlib.Path, cache_key: str = "") -> Optional[str]:
        """Get cached instrumented content if available."""
        if not cache_key:
            cache_key = self.get_cache_key(src_path)
        
        cache_file = self.cache_dir / f"{cache_key}.cached"
        
        if not cache_file.exists():
            return None
        
        try:
            cached_data = json.loads(cache_file.read_text(encoding="utf-8"))
            
            # Validate cache integrity
            if cached_data.get("telemetry_version") != self.telemetry_version:
                log.info(f"🗑️  Cache invalidated due to telemetry version change: {cache_file.name}")
                cache_file.unlink()
                return None
            
            if cached_data.get("original_hash") != self._get_file_hash(src_path):
                log.info(f"🗑️  Cache invalidated due to source change: {cache_file.name}")
                cache_file.unlink()
                return None
            
            return cached_data.get("instrumented_code")
        except Exception as e:
            log.warning(f"⚠️  Failed to read cache {cache_file.name}: {e}")
            return None
    
    def save_to_cache(self, src_path: pathlib.Path, instrumented_code: str, cache_key: str = ""):
        """Save instrumented code to cache with metadata."""
        if not cache_key:
            cache_key = self.get_cache_key(src_path)
        
        cache_file = self.cache_dir / f"{cache_key}.cached"
        
        cache_data = {
            "original_file": str(src_path),
            "original_hash": self._get_file_hash(src_path),
            "instrumented_code": instrumented_code,
            "telemetry_version": self.telemetry_version,
            "cache_timestamp": pathlib.Path().stat().st_mtime
        }
        
        try:
            cache_file.write_text(json.dumps(cache_data, indent=2), encoding="utf-8")
            log.debug(f"💾  Cached instrumented code: {cache_file.name}")
        except Exception as e:
            log.warning(f"⚠️  Failed to save cache {cache_file.name}: {e}")
    
    def _get_file_hash(self, file_path: pathlib.Path) -> str:
        """Get SHA256 hash of file content."""
        content = file_path.read_text(encoding="utf-8")
        return hashlib.sha256(content.encode()).hexdigest()
    
    def clear_cache(self):
        """Clear all cached files."""
        for cache_file in self.cache_dir.glob("*.cached"):
            cache_file.unlink()
        log.info("🗑️  Cache cleared")
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        cache_files = list(self.cache_dir.glob("*.cached"))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            "files": len(cache_files),
            "total_size_bytes": total_size,
            "telemetry_version": self.telemetry_version
        }
