"""
Knowledge Base module with dual storage (ChromaDB + PostgreSQL)
Supports button-based navigation with categories and subcategories
"""
import chromadb
import json
import logging
import os
from config import config
from typing import List, Dict, Optional
from .embedding import get_embedding_model, preload_embedding_model
import threading
import functools

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KnowledgeBase:
    """ChromaDB-based semantic knowledge base with PostgreSQL sync"""

    def __init__(self):
        self.persist_dir = config.CHROMA_PERSIST_DIR
        self.collection_name = config.CHROMA_COLLECTION_NAME
        self.embedding_model = None
        self.collection = None
        self._init_lock = threading.Lock()
        self._initialized = False
        self._categories_cache = None
        self._init_background()

    def _init_background(self):
        # Start background thread to preload embedding model and ChromaDB
        threading.Thread(target=self._initialize, daemon=True).start()

    def _initialize(self):
        with self._init_lock:
            if self._initialized:
                return
            preload_embedding_model()
            self.embedding_model = get_embedding_model()
            os.makedirs(self.persist_dir, exist_ok=True)
            logger.info(f"Persist directory: {self.persist_dir}")
            
            # Use PersistentClient for ChromaDB 1.x
            self.client = chromadb.PersistentClient(path=self.persist_dir)
            logger.info(f"ChromaDB client initialized with persist directory: {self.persist_dir}")
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "IT Support Knowledge Base"}
            )
            logger.info(f"Using collection: {self.collection_name}")
            self._initialized = True

    def _ensure_ready(self):
        # Block until background init is done
        while not self._initialized:
            import time
            time.sleep(0.1)
        if self.embedding_model is None or self.collection is None:
            raise RuntimeError("KnowledgeBase not initialized")
    
    def delete_all_entries(self):
        """Delete all entries from the knowledge base"""
        self._ensure_ready()
        try:
            # Get all IDs in collection
            results = self.collection.get()
            if results['ids']:
                self.collection.delete(ids=results['ids'])
                logger.info(f"Deleted {len(results['ids'])} entries from KB")
            # Clear cache
            self._cached_search.cache_clear()
            self._cached_embedding.cache_clear()
            self._categories_cache = None
            return True
        except Exception as e:
            logger.error(f"Failed to delete KB entries: {e}")
            return False
    
    def add_entry(self, issue: str, solution: str, source: str = "Admin Approved", 
                  entry_id: Optional[str] = None, category: str = None, 
                  subcategory: str = None, keywords: List[str] = None):
        """Add a new entry to the knowledge base"""
        self._ensure_ready()
        try:
            # Create embedding for the issue
            embedding = self.embedding_model.encode(issue).tolist()
            
            # Generate ID if not provided
            if entry_id is None:
                import uuid
                entry_id = f"kb_{uuid.uuid4().hex[:8]}"
            
            # Build metadata
            metadata = {
                "solution": solution,
                "source": source,
                "issue": issue,
                "category": category or "",
                "subcategory": subcategory or "",
                "keywords": ",".join(keywords) if keywords else ""
            }
            
            # Add to collection
            self.collection.add(
                ids=[entry_id],
                embeddings=[embedding],
                documents=[issue],
                metadatas=[metadata]
            )
            
            logger.info(f"Added KB entry: {entry_id}")
            # Clear cache
            self._cached_search.cache_clear()
            return entry_id
        except Exception as e:
            logger.error(f"Failed to add KB entry: {e}")
            return None

    @functools.lru_cache(maxsize=128)
    def _cached_embedding(self, text):
        return tuple(self.embedding_model.encode(text).tolist())

    @functools.lru_cache(maxsize=128)
    def _cached_search(self, query, top_k):
        # This is a tuple because lru_cache needs hashable args
        query_embedding = list(self._cached_embedding(query))
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        formatted_results = []
        if results['ids'] and len(results['ids'][0]) > 0:
            for idx in range(len(results['ids'][0])):
                metadata = results['metadatas'][0][idx]
                distance = results['distances'][0][idx] if 'distances' in results else 0
                confidence = max(0, 1 - distance)
                formatted_results.append({
                    'id': results['ids'][0][idx],
                    'issue': metadata.get('issue', ''),
                    'solution': metadata.get('solution', ''),
                    'source': metadata.get('source', ''),
                    'category': metadata.get('category', ''),
                    'subcategory': metadata.get('subcategory', ''),
                    'keywords': metadata.get('keywords', '').split(',') if metadata.get('keywords') else [],
                    'confidence': round(confidence, 3),
                    'distance': round(distance, 3)
                })
        return formatted_results

    def search(self, query: str, top_k: int = 1) -> List[Dict]:
        """Search knowledge base for relevant solutions (with LRU cache)"""
        self._ensure_ready()
        try:
            return self._cached_search(query, top_k)
        except Exception as e:
            logger.error(f"KB search failed: {e}")
            return []
    
    def search_by_category(self, category: str) -> List[Dict]:
        """Get all entries for a specific category"""
        self._ensure_ready()
        try:
            results = self.collection.get(
                where={"category": category}
            )
            formatted_results = []
            if results['ids']:
                for idx, entry_id in enumerate(results['ids']):
                    metadata = results['metadatas'][idx]
                    formatted_results.append({
                        'id': entry_id,
                        'issue': metadata.get('issue', ''),
                        'solution': metadata.get('solution', ''),
                        'source': metadata.get('source', ''),
                        'category': metadata.get('category', ''),
                        'subcategory': metadata.get('subcategory', ''),
                        'keywords': metadata.get('keywords', '').split(',') if metadata.get('keywords') else []
                    })
            return formatted_results
        except Exception as e:
            logger.error(f"Category search failed: {e}")
            return []
    
    def get_entry(self, entry_id: str) -> Optional[Dict]:
        """Get a specific entry by ID"""
        self._ensure_ready()
        try:
            result = self.collection.get(ids=[entry_id])
            if result['ids']:
                metadata = result['metadatas'][0]
                return {
                    'id': entry_id,
                    'issue': metadata.get('issue', ''),
                    'solution': metadata.get('solution', ''),
                    'source': metadata.get('source', ''),
                    'category': metadata.get('category', ''),
                    'subcategory': metadata.get('subcategory', ''),
                    'keywords': metadata.get('keywords', '').split(',') if metadata.get('keywords') else []
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get KB entry: {e}")
            return None
    
    def update_entry(self, entry_id: str, issue: str = None, solution: str = None, 
                     source: str = None, category: str = None, subcategory: str = None,
                     keywords: List[str] = None):
        """Update an existing KB entry"""
        self._ensure_ready()
        try:
            existing = self.get_entry(entry_id)
            if not existing:
                logger.warning(f"Entry {entry_id} not found for update")
                return False
            
            # Use existing values if new ones not provided
            new_issue = issue or existing['issue']
            new_solution = solution or existing['solution']
            new_source = source or existing['source']
            new_category = category if category is not None else existing['category']
            new_subcategory = subcategory if subcategory is not None else existing['subcategory']
            new_keywords = keywords if keywords is not None else existing['keywords']
            
            # Delete old entry
            self.collection.delete(ids=[entry_id])
            
            # Add updated entry
            self.add_entry(new_issue, new_solution, new_source, entry_id, 
                          new_category, new_subcategory, new_keywords)
            
            # Clear cache
            self._cached_search.cache_clear()
            logger.info(f"Updated KB entry: {entry_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update KB entry: {e}")
            return False
    
    def delete_entry(self, entry_id: str):
        """Delete an entry from KB"""
        self._ensure_ready()
        try:
            self.collection.delete(ids=[entry_id])
            # Clear cache
            self._cached_search.cache_clear()
            logger.info(f"Deleted KB entry: {entry_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete KB entry: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """Get knowledge base statistics"""
        self._ensure_ready()
        try:
            count = self.collection.count()
            return {
                'total_entries': count,
                'collection_name': self.collection_name,
                'embedding_model': config.EMBEDDING_MODEL
            }
        except Exception as e:
            logger.error(f"Failed to get KB stats: {e}")
            return {}
    
    def get_all_entries(self) -> List[Dict]:
        """Get all entries from the knowledge base"""
        self._ensure_ready()
        try:
            results = self.collection.get()
            formatted_results = []
            if results['ids']:
                for idx, entry_id in enumerate(results['ids']):
                    metadata = results['metadatas'][idx]
                    formatted_results.append({
                        'id': entry_id,
                        'issue': metadata.get('issue', ''),
                        'solution': metadata.get('solution', ''),
                        'source': metadata.get('source', ''),
                        'category': metadata.get('category', ''),
                        'subcategory': metadata.get('subcategory', ''),
                        'keywords': metadata.get('keywords', '').split(',') if metadata.get('keywords') else []
                    })
            return formatted_results
        except Exception as e:
            logger.error(f"Failed to get all KB entries: {e}")
            return []

    def load_kb_from_json(self, json_path: str = None) -> int:
        """Load knowledge base from data.json (hierarchical IT support data)"""
        self._ensure_ready()
        if json_path is None:
            json_path = os.path.join(os.path.dirname(__file__), 'data', 'data.json')
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            count = 0
            categories = data.get('categories', [])
            
            for category in categories:
                cat_name = category.get('name', '')
                subcategories = category.get('subcategories', [])
                
                for subcat in subcategories:
                    # Skip "Other Issues" free text mode
                    if subcat.get('solution') == 'FREE_TEXT_MODE':
                        continue
                    
                    entry_id = subcat.get('id')
                    title = subcat.get('title', '')
                    solution = subcat.get('solution', '')
                    keywords = subcat.get('keywords', [])
                    source = subcat.get('source', 'Knowledge Base')
                    
                    self.add_entry(
                        issue=title,
                        solution=solution,
                        source=source,
                        entry_id=entry_id,
                        category=cat_name,
                        subcategory=title,
                        keywords=keywords
                    )
                    count += 1
            
            logger.info(f"Loaded {count} entries from JSON")
            return count
        except Exception as e:
            logger.error(f"Failed to load KB from JSON: {e}")
            return 0
    
    def get_categories_structure(self) -> List[Dict]:
        """Get the category structure for button navigation"""
        json_path = os.path.join(os.path.dirname(__file__), 'data', 'initial_kb.json')
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            categories = []
            for cat in data.get('categories', []):
                categories.append({
                    'id': cat.get('id', ''),
                    'name': cat.get('name', ''),
                    'display_name': cat.get('display_name', ''),
                    'icon': cat.get('icon', ''),
                    'subcategories': [
                        {
                            'id': sub.get('id', ''),
                            'title': sub.get('title', ''),
                            'is_free_text': sub.get('solution') == 'FREE_TEXT_MODE'
                        }
                        for sub in cat.get('subcategories', [])
                    ]
                })
            
            return categories
        except Exception as e:
            logger.error(f"Failed to get categories structure: {e}")
            return []
    
    def get_solution_by_subcategory_id(self, subcat_id: str) -> Optional[Dict]:
        """Get solution for a specific subcategory ID"""
        json_path = os.path.join(os.path.dirname(__file__), 'data', 'initial_kb.json')
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for cat in data.get('categories', []):
                for sub in cat.get('subcategories', []):
                    if sub.get('id') == subcat_id:
                        return {
                            'id': sub.get('id'),
                            'title': sub.get('title'),
                            'solution': sub.get('solution'),
                            'source': sub.get('source'),
                            'category': cat.get('name'),
                            'is_free_text': sub.get('solution') == 'FREE_TEXT_MODE'
                        }
            return None
        except Exception as e:
            logger.error(f"Failed to get solution by subcategory ID: {e}")
            return None


# Global KB instance
kb = KnowledgeBase()