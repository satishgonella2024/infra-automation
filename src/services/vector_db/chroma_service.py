"""
ChromaDB Service for vector database operations.

This service interfaces with ChromaDB for storing and retrieving 
vector embeddings for various agents.
"""

import os
import uuid
import logging
import tempfile
from typing import Dict, List, Any, Optional

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

logger = logging.getLogger(__name__)

class ChromaService:
    """ChromaDB service for vector storage and retrieval."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Use a temporary directory for testing if TESTING environment variable is set
        if os.environ.get("TESTING") == "1":
            self.db_path = os.path.join(tempfile.gettempdir(), "chroma_test_data")
        else:
            self.db_path = os.environ.get("CHROMA_DB_PATH", "/app/chroma_data")
        
        # Create the directory if it doesn't exist
        os.makedirs(self.db_path, exist_ok=True)
        
        logger.info(f"Initializing ChromaDB client with persistent storage at {self.db_path}")
        
        # Use PersistentClient instead of HttpClient
        self.client = chromadb.PersistentClient(
            path=self.db_path,
            settings=Settings(anonymized_telemetry=False)  # Disable telemetry
        )
        
        # Default embedding function
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
        
        # Collection cache to avoid recreating collections
        self._collections = {}
        
        logger.info("ChromaDB service initialized")
        
    def get_collection(self, collection_name: str) -> Any:
        """Get or create a collection by name."""
        if collection_name in self._collections:
            return self._collections[collection_name]
        
        try:
            # Try to get existing collection
            collection = self.client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            self._collections[collection_name] = collection
            return collection
        except Exception as e:
            logger.info(f"Collection {collection_name} not found, creating: {e}")
            
            # Create new collection
            collection = self.client.create_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            self._collections[collection_name] = collection
            return collection
    
    async def store_document(
        self, 
        collection_name: str,
        document_id: str,
        text: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Store a document in the vector database.
        
        Args:
            collection_name: Name of the collection to store in
            document_id: Unique ID for the document
            text: Text content to embed and store
            metadata: Additional metadata for the document
            
        Returns:
            Dictionary with the document ID
        """
        try:
            collection = self.get_collection(collection_name)

            # Ensure metadata is not empty (ChromaDB requirement)
            if metadata is None or len(metadata) == 0:
                metadata = {"_default": "true"}  # Default non-empty metadata
            
            # Add document to collection
            collection.add(
                ids=[document_id],
                documents=[text],
                metadatas=[metadata or {}]
            )
            
            logger.info(f"Stored document {document_id} in collection {collection_name}")
            return {"id": document_id}
        except Exception as e:
            logger.error(f"Error storing document in ChromaDB: {e}")
            raise e
    
    async def query_similar(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = 5,
        where: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Query for similar documents.
        
        Args:
            collection_name: Name of the collection to query
            query_text: Text to find similar documents for
            n_results: Maximum number of results to return
            where: Optional filter conditions
            
        Returns:
            List of similar documents with metadata
        """
        try:
            collection = self.get_collection(collection_name)
            
            # Process where clause for ChromaDB format
            where_clause = None
            if where:
                # Convert simple dict to Chroma's where format
                # e.g., {"key": "value"} becomes {"$and": [{"key": {"$eq": "value"}}, ...]}
                where_conditions = []
                for key, value in where.items():
                    where_conditions.append({key: {"$eq": value}})
                
                if len(where_conditions) > 0:
                    if len(where_conditions) == 1:
                        where_clause = where_conditions[0]
                    else:
                        where_clause = {"$and": where_conditions}
            
            # Query collection
            results = collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where_clause
            )
            
            # Format results
            formatted_results = []
            if results and 'documents' in results and results['documents']:
                documents = results['documents'][0]
                metadatas = results['metadatas'][0]
                ids = results['ids'][0]
                distances = results.get('distances', [[0] * len(documents)])[0]
                
                for i in range(len(documents)):
                    formatted_results.append({
                        "id": ids[i],
                        "content": documents[i],
                        "metadata": metadatas[i],
                        "similarity": 1.0 - (distances[i] if distances[i] <= 1.0 else 0.0)
                    })
            
            return formatted_results
        except Exception as e:
            logger.error(f"Error querying ChromaDB: {e}")
            return []
    
    async def delete_document(self, collection_name: str, document_id: str) -> Dict[str, Any]:
        """
        Delete a document from the database.
        
        Args:
            collection_name: Name of the collection
            document_id: ID of the document to delete
            
        Returns:
            Dictionary with the document ID
        """
        try:
            collection = self.get_collection(collection_name)
            collection.delete(ids=[document_id])
            logger.info(f"Deleted document {document_id} from collection {collection_name}")
            return {"id": document_id}
        except Exception as e:
            logger.error(f"Error deleting document from ChromaDB: {e}")
            raise e
    
    async def update_document(
        self,
        collection_name: str,
        document_id: str,
        text: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Update a document in the database.
        
        Args:
            collection_name: Name of the collection
            document_id: ID of the document to update
            text: New text content
            metadata: New metadata
            
        Returns:
            Dictionary with the document ID
        """
        try:
            collection = self.get_collection(collection_name)

            # Ensure metadata is not empty (ChromaDB requirement)
            if metadata is None or len(metadata) == 0:
                metadata = {"_default": "true"}  # Default non-empty metadata
                
            collection.update(
                ids=[document_id],
                documents=[text],
                metadatas=[metadata or {}]
            )
            logger.info(f"Updated document {document_id} in collection {collection_name}")
            return {"id": document_id}
        except Exception as e:
            logger.error(f"Error updating document in ChromaDB: {e}")
            raise e
    
    async def list_collections(self) -> List[str]:
        """List all collections in the database."""
        try:
            collections = self.client.list_collections()
            return [collection.name for collection in collections]
        except Exception as e:
            # Handling for ChromaDB v0.6.0+ compatibility
            try:
                collections = self.client.list_collections()
                if isinstance(collections[0], str):
                    return collections
                return [collection.name for collection in collections]
            except Exception as nested_e:
                logger.error(f"Error listing collections from ChromaDB: {nested_e}")
                return []
            
    # Pattern-specific methods for API endpoints
    
    async def add_pattern(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a new infrastructure pattern to the database.
        
        Args:
            pattern: Dictionary containing pattern data
            
        Returns:
            Dictionary with the pattern ID
        """
        # Generate a UUID if not provided
        pattern_id = pattern.get("id", str(uuid.uuid4()))
        
        # Extract pattern data
        name = pattern.get("name", "")
        description = pattern.get("description", "")
        cloud_provider = pattern.get("cloud_provider", "")
        iac_type = pattern.get("iac_type", "")
        code = pattern.get("code", "")
        metadata = pattern.get("metadata", {})
        
        # Combine all metadata
        combined_metadata = {
            "name": name,
            "description": description,
            "cloud_provider": cloud_provider,
            "iac_type": iac_type,
            **metadata
        }
        
        # Store the document
        return await self.store_document(
            collection_name="infrastructure_patterns",
            document_id=pattern_id,
            text=code,
            metadata=combined_metadata
        )
    
    async def search_patterns(
        self, 
        query: str, 
        cloud_provider: str = None, 
        iac_type: str = None,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for infrastructure patterns similar to the query.
        
        Args:
            query: The search query
            cloud_provider: Optional filter for cloud provider
            iac_type: Optional filter for IaC type
            n_results: Maximum number of results to return
            
        Returns:
            List of similar patterns with metadata
        """
        # Build the where clause
        where = {}
        if cloud_provider:
            where["cloud_provider"] = cloud_provider
        if iac_type:
            where["iac_type"] = iac_type
        
        # Query for similar patterns
        results = await self.query_similar(
            collection_name="infrastructure_patterns",
            query_text=query,
            n_results=n_results,
            where=where if where else None
        )
        
        # Format the results
        formatted_results = []
        for result in results:
            formatted_results.append({
                "id": result["id"],
                "name": result["metadata"].get("name", ""),
                "description": result["metadata"].get("description", ""),
                "cloud_provider": result["metadata"].get("cloud_provider", ""),
                "iac_type": result["metadata"].get("iac_type", ""),
                "code": result["content"],
                "metadata": {k: v for k, v in result["metadata"].items() 
                            if k not in ["name", "description", "cloud_provider", "iac_type"]}
            })
        
        return formatted_results
    
    async def get_pattern(self, pattern_id: str) -> Dict[str, Any]:
        """
        Get a pattern by ID.
        
        Args:
            pattern_id: ID of the pattern to get
            
        Returns:
            Pattern data
        """
        try:
            collection = self.get_collection("infrastructure_patterns")
            result = collection.get(ids=[pattern_id])
            
            if not result or not result["ids"]:
                return None
            
            # Format the result
            metadata = result["metadatas"][0]
            return {
                "id": result["ids"][0],
                "name": metadata.get("name", ""),
                "description": metadata.get("description", ""),
                "cloud_provider": metadata.get("cloud_provider", ""),
                "iac_type": metadata.get("iac_type", ""),
                "code": result["documents"][0],
                "metadata": {k: v for k, v in metadata.items() 
                           if k not in ["name", "description", "cloud_provider", "iac_type"]}
            }
        except Exception as e:
            logger.error(f"Error getting pattern from ChromaDB: {e}")
            return None
    
    async def update_pattern(self, pattern_id: str, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing infrastructure pattern.
        
        Args:
            pattern_id: ID of the pattern to update
            pattern: Dictionary containing updated pattern data
            
        Returns:
            Dictionary with the pattern ID
        """
        # Extract pattern data
        name = pattern.get("name", "")
        description = pattern.get("description", "")
        cloud_provider = pattern.get("cloud_provider", "")
        iac_type = pattern.get("iac_type", "")
        code = pattern.get("code", "")
        metadata = pattern.get("metadata", {})
        
        # Combine all metadata
        combined_metadata = {
            "name": name,
            "description": description,
            "cloud_provider": cloud_provider,
            "iac_type": iac_type,
            **metadata
        }
        
        # Update the document
        return await self.update_document(
            collection_name="infrastructure_patterns",
            document_id=pattern_id,
            text=code,
            metadata=combined_metadata
        )
    
    async def delete_pattern(self, pattern_id: str) -> Dict[str, Any]:
        """
        Delete an infrastructure pattern.
        
        Args:
            pattern_id: ID of the pattern to delete
            
        Returns:
            Dictionary with the pattern ID
        """
        return await self.delete_document(
            collection_name="infrastructure_patterns",
            document_id=pattern_id
        )