"""
BigQuery Database Connector
"""
from typing import Optional
from google.cloud import bigquery
from google.oauth2 import service_account

from api.app.services.database.base import BaseDatabaseConnector


class BigQueryConnector(BaseDatabaseConnector):
    """Google BigQuery connector"""
    
    def __init__(
        self,
        host: str,  # project_id or path to service account JSON
        port: int,
        username: str,
        password: str,  # Can be JSON key content or empty
        database: str  # dataset_id
    ):
        self.project_id = host
        self.dataset_id = database
        self.credentials_json = password  # Service account JSON or empty
        self._client: Optional[bigquery.Client] = None
    
    async def connect(self) -> bool:
        """Establish connection to BigQuery"""
        try:
            if self.credentials_json:
                # If credentials provided as JSON string
                import json
                credentials_dict = json.loads(self.credentials_json)
                credentials = service_account.Credentials.from_service_account_info(
                    credentials_dict
                )
                self._client = bigquery.Client(
                    credentials=credentials,
                    project=self.project_id
                )
            else:
                # Use default credentials (ADC)
                self._client = bigquery.Client(project=self.project_id)
            
            return True
        except Exception as e:
            raise ConnectionError(f"Failed to connect to BigQuery: {str(e)}")
    
    async def disconnect(self) -> None:
        """Close BigQuery connection"""
        if self._client:
            self._client.close()
            self._client = None
    
    async def test_connection(self) -> tuple[bool, str]:
        """Test BigQuery connection"""
        try:
            await self.connect()
            # Test query to verify connection
            query = "SELECT 1 as test"
            query_job = self._client.query(query)
            list(query_job.result())
            await self.disconnect()
            return True, f"Connected successfully to BigQuery project: {self.project_id}"
        except Exception as e:
            return False, str(e)
    
    async def get_tables(self) -> list[str]:
        """Get list of tables from BigQuery dataset"""
        if not self._client:
            await self.connect()
        
        dataset_ref = self._client.dataset(self.dataset_id)
        tables = list(self._client.list_tables(dataset_ref))
        return [table.table_id for table in tables]
    
    async def get_schema(self) -> str:
        """Get BigQuery schema DDL"""
        if not self._client:
            await self.connect()
        
        tables = await self.get_tables()
        schema_ddl = []
        
        for table_id in tables:
            table_ref = self._client.dataset(self.dataset_id).table(table_id)
            table = self._client.get_table(table_ref)
            
            ddl = f"CREATE TABLE {table_id} (\n"
            col_defs = []
            
            for field in table.schema:
                col_def = f"  {field.name} {field.field_type}"
                
                if field.mode == "REQUIRED":
                    col_def += " NOT NULL"
                
                if field.description:
                    col_def += f" -- {field.description}"
                
                col_defs.append(col_def)
            
            ddl += ",\n".join(col_defs) + "\n)"
            schema_ddl.append(ddl)
        
        return ";\n\n".join(schema_ddl) + ";"
    
    async def execute_query(self, query: str) -> tuple[list[str], list[dict]]:
        """Execute a read-only SQL query"""
        self._validate_read_only(query)
        
        if not self._client:
            await self.connect()
        
        # Add fully qualified table names if not present
        query_job = self._client.query(query)
        results = query_job.result()
        
        columns = [field.name for field in results.schema]
        rows = []
        
        for row in results:
            rows.append(dict(zip(columns, row.values())))
        
        return columns, rows
