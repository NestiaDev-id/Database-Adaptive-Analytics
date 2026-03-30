"""
MySQL Database Connector
"""
import pymysql
from pymysql.cursors import DictCursor

from api.app.services.database.base import BaseDatabaseConnector


class MySQLConnector(BaseDatabaseConnector):
    """MySQL database connector"""
    
    async def connect(self) -> bool:
        """Establish connection to MySQL"""
        try:
            self._connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.username,
                password=self.password,
                database=self.database,
                cursorclass=DictCursor
            )
            return True
        except Exception as e:
            raise ConnectionError(f"Failed to connect to MySQL: {str(e)}")
    
    async def disconnect(self) -> None:
        """Close MySQL connection"""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    async def test_connection(self) -> tuple[bool, str]:
        """Test MySQL connection"""
        try:
            await self.connect()
            cursor = self._connection.cursor()
            cursor.execute("SELECT VERSION();")
            version = cursor.fetchone()
            cursor.close()
            await self.disconnect()
            return True, f"Connected successfully. MySQL {list(version.values())[0]}"
        except Exception as e:
            return False, str(e)
    
    async def get_tables(self) -> list[str]:
        """Get list of table names from MySQL"""
        if not self._connection:
            await self.connect()
        
        cursor = self._connection.cursor()
        cursor.execute("SHOW TABLES;")
        tables = [list(row.values())[0] for row in cursor.fetchall()]
        cursor.close()
        return tables
    
    async def get_schema(self) -> str:
        """Get MySQL schema as DDL"""
        if not self._connection:
            await self.connect()
        
        cursor = self._connection.cursor()
        tables = await self.get_tables()
        
        ddl_statements = []
        for table in tables:
            cursor.execute(f"SHOW CREATE TABLE `{table}`;")
            result = cursor.fetchone()
            if result:
                ddl = list(result.values())[1]
                ddl_statements.append(ddl + ";")
        
        cursor.close()
        return "\n\n".join(ddl_statements)
    
    async def execute_query(self, query: str) -> tuple[list[str], list[dict]]:
        """Execute a read-only SQL query on MySQL"""
        if not self._validate_read_only(query):
            raise ValueError("Only SELECT queries are allowed (read-only mode)")
        
        if not self._connection:
            await self.connect()
        
        cursor = self._connection.cursor()
        cursor.execute(query)
        
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = list(cursor.fetchall())
        
        cursor.close()
        return columns, rows
