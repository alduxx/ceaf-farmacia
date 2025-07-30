"""
Caching mechanism for CEAF data to reduce server load and improve performance.
"""

import json
import os
import time
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, List
from pathlib import Path

try:
    import diskcache as dc
    DISKCACHE_AVAILABLE = True
except ImportError:
    DISKCACHE_AVAILABLE = False
    logging.warning("diskcache not available. Using file-based caching fallback.")


class CacheManager:
    """Manages caching for scraped data and processed results."""
    
    def __init__(self, cache_dir: str = "cache", default_ttl: int = 3600):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.default_ttl = default_ttl  # Time to live in seconds
        self.logger = logging.getLogger(__name__)
        
        # Initialize disk cache if available
        if DISKCACHE_AVAILABLE:
            self.disk_cache = dc.Cache(str(self.cache_dir / "diskcache"))
        else:
            self.disk_cache = None
            
        # Ensure subdirectories exist
        (self.cache_dir / "scraped").mkdir(exist_ok=True)
        (self.cache_dir / "processed").mkdir(exist_ok=True)
        (self.cache_dir / "search").mkdir(exist_ok=True)
    
    def _get_cache_key(self, key: str, prefix: str = "") -> str:
        """Generate a cache key with optional prefix."""
        if prefix:
            key = f"{prefix}:{key}"
        return hashlib.md5(key.encode()).hexdigest()
    
    def _is_expired(self, timestamp: float, ttl: int) -> bool:
        """Check if cached data has expired."""
        return time.time() - timestamp > ttl
    
    def _get_file_path(self, cache_type: str, key: str) -> Path:
        """Get the file path for a cache entry."""
        cache_key = self._get_cache_key(key)
        return self.cache_dir / cache_type / f"{cache_key}.json"
    
    def set_scraped_data(self, url: str, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Cache scraped data from a URL."""
        ttl = ttl or self.default_ttl
        
        cache_entry = {
            "url": url,
            "data": data,
            "cached_at": time.time(),
            "ttl": ttl,
            "expires_at": time.time() + ttl
        }
        
        # Try disk cache first
        if self.disk_cache:
            try:
                cache_key = self._get_cache_key(url, "scraped")
                self.disk_cache.set(cache_key, cache_entry, expire=ttl)
                self.logger.info(f"Cached scraped data for {url} (disk cache)")
                return True
            except Exception as e:
                self.logger.warning(f"Disk cache failed for {url}: {e}")
        
        # Fallback to file cache
        try:
            file_path = self._get_file_path("scraped", url)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(cache_entry, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Cached scraped data for {url} (file cache)")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cache scraped data for {url}: {e}")
            return False
    
    def get_scraped_data(self, url: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached scraped data for a URL."""
        
        # Try disk cache first
        if self.disk_cache:
            try:
                cache_key = self._get_cache_key(url, "scraped")
                cache_entry = self.disk_cache.get(cache_key)
                if cache_entry:
                    self.logger.info(f"Retrieved scraped data for {url} (disk cache)")
                    return cache_entry["data"]
            except Exception as e:
                self.logger.warning(f"Disk cache retrieval failed for {url}: {e}")
        
        # Fallback to file cache
        try:
            file_path = self._get_file_path("scraped", url)
            if not file_path.exists():
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                cache_entry = json.load(f)
            
            # Check if expired
            if self._is_expired(cache_entry["cached_at"], cache_entry["ttl"]):
                self.logger.info(f"Cache expired for {url}, removing")
                file_path.unlink(missing_ok=True)
                return None
            
            self.logger.info(f"Retrieved scraped data for {url} (file cache)")
            return cache_entry["data"]
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve cached data for {url}: {e}")
            return None
    
    def set_processed_data(self, data_hash: str, processed_data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Cache processed data with a hash of the original data."""
        ttl = ttl or self.default_ttl * 2  # Processed data can be cached longer
        
        cache_entry = {
            "data_hash": data_hash,
            "processed_data": processed_data,
            "cached_at": time.time(),
            "ttl": ttl,
            "expires_at": time.time() + ttl
        }
        
        # Try disk cache first
        if self.disk_cache:
            try:
                cache_key = self._get_cache_key(data_hash, "processed")
                self.disk_cache.set(cache_key, cache_entry, expire=ttl)
                self.logger.info(f"Cached processed data for hash {data_hash[:8]}... (disk cache)")
                return True
            except Exception as e:
                self.logger.warning(f"Disk cache failed for processed data: {e}")
        
        # Fallback to file cache
        try:
            file_path = self._get_file_path("processed", data_hash)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(cache_entry, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Cached processed data for hash {data_hash[:8]}... (file cache)")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cache processed data: {e}")
            return False
    
    def get_processed_data(self, data_hash: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached processed data by hash."""
        
        # Try disk cache first
        if self.disk_cache:
            try:
                cache_key = self._get_cache_key(data_hash, "processed")
                cache_entry = self.disk_cache.get(cache_key)
                if cache_entry:
                    self.logger.info(f"Retrieved processed data for hash {data_hash[:8]}... (disk cache)")
                    return cache_entry["processed_data"]
            except Exception as e:
                self.logger.warning(f"Disk cache retrieval failed for processed data: {e}")
        
        # Fallback to file cache
        try:
            file_path = self._get_file_path("processed", data_hash)
            if not file_path.exists():
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                cache_entry = json.load(f)
            
            # Check if expired
            if self._is_expired(cache_entry["cached_at"], cache_entry["ttl"]):
                self.logger.info(f"Processed cache expired for hash {data_hash[:8]}..., removing")
                file_path.unlink(missing_ok=True)
                return None
            
            self.logger.info(f"Retrieved processed data for hash {data_hash[:8]}... (file cache)")
            return cache_entry["processed_data"]
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve cached processed data: {e}")
            return None
    
    def set_search_results(self, query: str, results: List[Dict[str, Any]], ttl: Optional[int] = None) -> bool:
        """Cache search results for a query."""
        ttl = ttl or 1800  # Search results cached for 30 minutes
        
        cache_entry = {
            "query": query,
            "results": results,
            "cached_at": time.time(),
            "ttl": ttl,
            "expires_at": time.time() + ttl
        }
        
        # Use shorter TTL for search results
        if self.disk_cache:
            try:
                cache_key = self._get_cache_key(query.lower(), "search")
                self.disk_cache.set(cache_key, cache_entry, expire=ttl)
                self.logger.info(f"Cached search results for '{query}' (disk cache)")
                return True
            except Exception as e:
                self.logger.warning(f"Disk cache failed for search '{query}': {e}")
        
        # Fallback to file cache
        try:
            file_path = self._get_file_path("search", query.lower())
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(cache_entry, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Cached search results for '{query}' (file cache)")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cache search results for '{query}': {e}")
            return False
    
    def get_search_results(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """Retrieve cached search results for a query."""
        
        # Try disk cache first
        if self.disk_cache:
            try:
                cache_key = self._get_cache_key(query.lower(), "search")
                cache_entry = self.disk_cache.get(cache_key)
                if cache_entry:
                    self.logger.info(f"Retrieved search results for '{query}' (disk cache)")
                    return cache_entry["results"]
            except Exception as e:
                self.logger.warning(f"Disk cache retrieval failed for search '{query}': {e}")
        
        # Fallback to file cache
        try:
            file_path = self._get_file_path("search", query.lower())
            if not file_path.exists():
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                cache_entry = json.load(f)
            
            # Check if expired
            if self._is_expired(cache_entry["cached_at"], cache_entry["ttl"]):
                self.logger.info(f"Search cache expired for '{query}', removing")
                file_path.unlink(missing_ok=True)
                return None
            
            self.logger.info(f"Retrieved search results for '{query}' (file cache)")
            return cache_entry["results"]
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve cached search results for '{query}': {e}")
            return None
    
    def clear_expired(self) -> int:
        """Clear all expired cache entries. Returns number of entries cleared."""
        cleared_count = 0
        
        # Clear disk cache expired entries (automatic with diskcache)
        if self.disk_cache:
            try:
                # diskcache handles expiration automatically
                pass
            except Exception as e:
                self.logger.error(f"Error during disk cache cleanup: {e}")
        
        # Clear expired file cache entries
        for cache_type in ["scraped", "processed", "search"]:
            cache_type_dir = self.cache_dir / cache_type
            if not cache_type_dir.exists():
                continue
                
            for cache_file in cache_type_dir.glob("*.json"):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_entry = json.load(f)
                    
                    if self._is_expired(cache_entry["cached_at"], cache_entry["ttl"]):
                        cache_file.unlink()
                        cleared_count += 1
                        
                except Exception as e:
                    self.logger.warning(f"Error checking cache file {cache_file}: {e}")
                    # Remove corrupted cache files
                    cache_file.unlink(missing_ok=True)
                    cleared_count += 1
        
        if cleared_count > 0:
            self.logger.info(f"Cleared {cleared_count} expired cache entries")
        
        return cleared_count
    
    def clear_all(self) -> bool:
        """Clear all cache entries."""
        try:
            # Clear disk cache
            if self.disk_cache:
                self.disk_cache.clear()
            
            # Clear file cache
            for cache_type in ["scraped", "processed", "search"]:
                cache_type_dir = self.cache_dir / cache_type
                if cache_type_dir.exists():
                    for cache_file in cache_type_dir.glob("*.json"):
                        cache_file.unlink()
            
            self.logger.info("Cleared all cache entries")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to clear cache: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = {
            "cache_dir": str(self.cache_dir),
            "disk_cache_available": DISKCACHE_AVAILABLE,
            "file_cache_entries": 0,
            "total_cache_size_mb": 0,
            "cache_types": {}
        }
        
        # Count file cache entries and calculate size
        for cache_type in ["scraped", "processed", "search"]:
            cache_type_dir = self.cache_dir / cache_type
            if not cache_type_dir.exists():
                continue
                
            cache_files = list(cache_type_dir.glob("*.json"))
            cache_size = sum(f.stat().st_size for f in cache_files)
            
            stats["cache_types"][cache_type] = {
                "entries": len(cache_files),
                "size_mb": cache_size / (1024 * 1024)
            }
            
            stats["file_cache_entries"] += len(cache_files)
            stats["total_cache_size_mb"] += cache_size / (1024 * 1024)
        
        # Disk cache stats
        if self.disk_cache:
            try:
                stats["disk_cache_size_mb"] = self.disk_cache.volume() / (1024 * 1024)
            except Exception:
                stats["disk_cache_size_mb"] = 0
        
        return stats
    
    def generate_data_hash(self, data: Any) -> str:
        """Generate a hash for data to use as cache key."""
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode()).hexdigest()


# Global cache instance
cache_manager = CacheManager()


def main():
    """Test cache functionality."""
    cache = CacheManager()
    
    # Test scraped data caching
    test_url = "https://example.com"
    test_data = {"conditions": ["test1", "test2"], "scraped_at": datetime.now().isoformat()}
    
    print("Testing cache functionality...")
    
    # Set and get scraped data
    cache.set_scraped_data(test_url, test_data, ttl=60)
    retrieved_data = cache.get_scraped_data(test_url)
    print(f"Scraped data cache test: {'PASS' if retrieved_data == test_data else 'FAIL'}")
    
    # Test processed data caching
    data_hash = cache.generate_data_hash(test_data)
    processed_data = {"categories": {"test": {"conditions": ["test1"]}}}
    
    cache.set_processed_data(data_hash, processed_data, ttl=60)
    retrieved_processed = cache.get_processed_data(data_hash)
    print(f"Processed data cache test: {'PASS' if retrieved_processed == processed_data else 'FAIL'}")
    
    # Test search results caching
    search_query = "diabetes"
    search_results = [{"name": "Diabetes Mellitus", "url": "http://example.com"}]
    
    cache.set_search_results(search_query, search_results, ttl=60)
    retrieved_search = cache.get_search_results(search_query)
    print(f"Search cache test: {'PASS' if retrieved_search == search_results else 'FAIL'}")
    
    # Display cache stats
    stats = cache.get_cache_stats()
    print(f"\nCache Statistics:")
    print(f"  Total entries: {stats['file_cache_entries']}")
    print(f"  Total size: {stats['total_cache_size_mb']:.2f} MB")
    print(f"  Disk cache available: {stats['disk_cache_available']}")
    
    # Clean up test data
    cache.clear_all()
    print("\nTest cache cleared.")


if __name__ == "__main__":
    main()