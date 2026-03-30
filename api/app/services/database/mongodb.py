"""
MongoDB Database Connector
"""
from typing import Optional
from pymongo import MongoClient

from api.app.services.database.base import BaseDatabaseConnector


class MongoDBConnector(BaseDatabaseConnector):
    """MongoDB database connector"""
    
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        database: str
    ):
        super().__init__(host, port, username, password, database)
        self._client: Optional[MongoClient] = None
        self._db = None
    
    async def connect(self) -> bool:
        """Establish connection to MongoDB"""
        try:
            # Fallback to connection_string if it looks like a URI
            from api.app.utils.config import settings
            
            # 1. Priority: full connection string
            # We need to get it from the factory or passed down. 
            # I will modify the factory to pass it if available.
            
            # For now, let's assume we might have it in host if it starts with mongodb
            if self.host.startswith("mongodb"):
                uri = self.host
            else:
                # Build connection string
                if self.username and self.password:
                    uri = f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
                else:
                    uri = f"mongodb://{self.host}:{self.port}/{self.database}"
            
            self._client = MongoClient(uri)
            
            # If database name is provided explicitly, use it
            if self.database:
                self._db = self._client[self.database]
            else:
                # Otherwise try to get it from the URI
                try:
                    self._db = self._client.get_database()
                    self.database = self._db.name
                except Exception:
                    raise ValueError("Database name is missing. Please provide it in the input/env or include it in the URI path.")
            
            # Test connection
            self._client.admin.command('ping')
            return True
        except Exception as e:
            raise ConnectionError(f"Failed to connect to MongoDB: {str(e)}")
    
    async def disconnect(self) -> None:
        """Close MongoDB connection"""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
    
    async def test_connection(self) -> tuple[bool, str]:
        """Test MongoDB connection"""
        try:
            await self.connect()
            server_info = self._client.server_info()
            version = server_info.get('version', 'unknown')
            await self.disconnect()
            return True, f"Connected successfully. MongoDB {version}"
        except Exception as e:
            return False, str(e)
    
    async def get_tables(self) -> list[str]:
        """Get list of collection names from MongoDB"""
        if not self._client:
            await self.connect()
        
        return self._db.list_collection_names()
    
    async def get_schema(self) -> str:
        """Get MongoDB schema (collection structure based on sample documents)"""
        if not self._client:
            await self.connect()
        
        collections = await self.get_tables()
        schema_docs = []
        
        for collection in collections:
            coll = self._db[collection]
            # Get sample document to infer schema
            sample = coll.find_one()
            
            if sample:
                fields = []
                for key, value in sample.items():
                    field_type = type(value).__name__
                    fields.append(f"  {key}: {field_type}")
                
                schema_doc = f"Collection: {collection}\nFields:\n" + "\n".join(fields)
                schema_docs.append(schema_doc)
            else:
                schema_docs.append(f"Collection: {collection}\n  (empty collection)")
        
        return "\n\n".join(schema_docs)
    
    async def execute_query(self, query: str) -> tuple[list[str], list[dict]]:
        """
        Execute a MongoDB query.
        Supports:
        1. Shell command string: db.collection.find({...})
        2. Shell command string: db.collection.aggregate([...])
        3. Legacy format: collection:operation:filter
        """
        if not self._client:
            await self.connect()
        
        # Clean query
        query = query.strip()
        
        collection_name = None
        operation = None
        filter_data = None
        limit_val = 100
        sort_data = None
        projection = None

        try:
            import json
            import re

            # Case A: Shell command db.collection.find(...)
            find_match = re.match(r'db\.(\w+)\.find\((.*?)\)(?:\.sort\((.*?)\))?(?:\.limit\((\d+)\))?', query)
            if find_match:
                collection_name = find_match.group(1)
                operation = "find"
                args_str = find_match.group(2).strip()
                
                # Parse find arguments (filter, projection)
                if args_str:
                    # Basic parser for two comma-separated JSON objects
                    # This is naive but works for our generated queries
                    if args_str.startswith('{'):
                        # Find the matching closing brace for the first object
                        depth = 0
                        split_idx = -1
                        for i, char in enumerate(args_str):
                            if char == '{': depth += 1
                            elif char == '}': 
                                depth -= 1
                                if depth == 0:
                                    split_idx = i + 1
                                    break
                        
                        if split_idx != -1 and split_idx < len(args_str):
                            f_part = args_str[:split_idx]
                            p_part = args_str[split_idx:].strip().lstrip(',')
                            filter_data = json.loads(f_part)
                            if p_part.strip():
                                projection = json.loads(p_part.strip())
                        else:
                            filter_data = json.loads(args_str)
                else:
                    filter_data = {}
                
                # Parse sort
                if find_match.group(3):
                    sort_data = json.loads(find_match.group(3))
                
                # Parse limit
                if find_match.group(4):
                    limit_val = int(find_match.group(4))

            # Case B: Shell command db.collection.aggregate(...)
            elif "aggregate(" in query:
                agg_match = re.match(r'db\.(\w+)\.aggregate\(([\s\S]*)\)', query)
                if agg_match:
                    collection_name = agg_match.group(1)
                    operation = "aggregate"
                    filter_data = json.loads(agg_match.group(2).strip())

            # Case C: Legacy format collection:operation:filter
            elif ":" in query:
                parts = query.split(":", 2)
                collection_name = parts[0].strip()
                operation = parts[1].strip().lower()
                filter_str = parts[2].strip() if len(parts) > 2 else "{}"
                filter_data = json.loads(filter_str) if filter_str else {}

            if not collection_name or not operation:
                raise ValueError("Unsupported or malformed MongoDB query format. "
                                 "Expected db.coll.find() or db.coll.aggregate().")

            # Execution
            coll = self._db[collection_name]
            rows = []
            
            if operation == "find":
                cursor = coll.find(filter_data or {}, projection)
                if sort_data:
                    # Convert dict to list of tuples for pymongo sort
                    sort_list = [(k, v) for k, v in sort_data.items()]
                    cursor = cursor.sort(sort_list)
                
                cursor = cursor.limit(limit_val)
                for doc in cursor:
                    doc['_id'] = str(doc['_id'])
                    rows.append(doc)
                
            elif operation == "aggregate":
                cursor = coll.aggregate(filter_data)
                for doc in cursor:
                    if '_id' in doc:
                        doc['_id'] = str(doc['_id'])
                    rows.append(doc)
            
            elif operation == "count":
                count = coll.count_documents(filter_data or {})
                return ["count"], [{"count": count}]
            
            columns = list(rows[0].keys()) if rows else []
            return columns, rows
                
        except Exception as e:
            raise ValueError(f"MongoDB query error: {str(e)}")
