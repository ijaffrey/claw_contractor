import logging
from typing import Dict, List, Any, Optional, Tuple
from database import get_db_session, Lead, LeadStatus, Base, NotificationLog

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    A comprehensive database manager that provides a unified interface for database operations.
    Handles connection management, query execution, and CRUD operations.
    """
    
    def __init__(self):
        """Initialize the DatabaseManager."""
        self.connection = None
        logger.info("DatabaseManager initialized")
    
    def create_connection(self) -> bool:
        """
        Create a database connection.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.connection = get_db_connection()
            if self.connection:
                logger.info("Database connection established successfully")
                return True
            else:
                logger.error("Failed to establish database connection")
                return False
        except Exception as e:
            logger.error(f"Error creating database connection: {str(e)}")
            return False
    
    def close_connection(self) -> bool:
        """
        Close the database connection.
        
        Returns:
            bool: True if connection closed successfully, False otherwise
        """
        try:
            if self.connection:
                close_db_connection(self.connection)
                self.connection = None
                logger.info("Database connection closed successfully")
                return True
            else:
                logger.warning("No active connection to close")
                return True
        except Exception as e:
            logger.error(f"Error closing database connection: {str(e)}")
            return False
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> bool:
        """
        Execute a SQL query (INSERT, UPDATE, DELETE, CREATE, etc.).
        
        Args:
            query (str): SQL query to execute
            params (Optional[Tuple]): Parameters for parameterized query
        
        Returns:
            bool: True if query executed successfully, False otherwise
        """
        if not self.connection:
            if not self.create_connection():
                return False
        
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            self.connection.commit()
            cursor.close()
            logger.info(f"Query executed successfully: {query[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def fetch_one(self, query: str, params: Optional[Tuple] = None) -> Optional[Dict[str, Any]]:
        """
        Execute a SELECT query and fetch one row.
        
        Args:
            query (str): SQL SELECT query
            params (Optional[Tuple]): Parameters for parameterized query
        
        Returns:
            Optional[Dict[str, Any]]: Single row as dictionary or None
        """
        if not self.connection:
            if not self.create_connection():
                return None
        
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Get column names
            columns = [description[0] for description in cursor.description]
            
            # Fetch one row
            row = cursor.fetchone()
            cursor.close()
            
            if row:
                result = dict(zip(columns, row))
                logger.info(f"Fetched one record successfully")
                return result
            else:
                logger.info("No record found")
                return None
        except Exception as e:
            logger.error(f"Error fetching one record: {str(e)}")
            return None
    
    def fetch_all(self, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query and fetch all rows.
        
        Args:
            query (str): SQL SELECT query
            params (Optional[Tuple]): Parameters for parameterized query
        
        Returns:
            List[Dict[str, Any]]: List of rows as dictionaries
        """
        if not self.connection:
            if not self.create_connection():
                return []
        
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Get column names
            columns = [description[0] for description in cursor.description]
            
            # Fetch all rows
            rows = cursor.fetchall()
            cursor.close()
            
            # Convert to list of dictionaries
            results = []
            for row in rows:
                results.append(dict(zip(columns, row)))
            
            logger.info(f"Fetched {len(results)} records successfully")
            return results
        except Exception as e:
            logger.error(f"Error fetching all records: {str(e)}")
            return []
    
    def insert_record(self, table: str, data: Dict[str, Any]) -> bool:
        """
        Insert a new record into the specified table.
        
        Args:
            table (str): Table name
            data (Dict[str, Any]): Dictionary of column names and values
        
        Returns:
            bool: True if insert successful, False otherwise
        """
        if not data:
            logger.warning("No data provided for insert operation")
            return False
        
        try:
            columns = list(data.keys())
            values = list(data.values())
            placeholders = ', '.join(['?' for _ in values])
            
            query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
            
            result = self.execute_query(query, tuple(values))
            if result:
                logger.info(f"Record inserted successfully into {table}")
            return result
        except Exception as e:
            logger.error(f"Error inserting record into {table}: {str(e)}")
            return False
    
    def update_record(self, table: str, data: Dict[str, Any], where_clause: str, where_params: Optional[Tuple] = None) -> bool:
        """
        Update records in the specified table.
        
        Args:
            table (str): Table name
            data (Dict[str, Any]): Dictionary of column names and new values
            where_clause (str): WHERE clause (without WHERE keyword)
            where_params (Optional[Tuple]): Parameters for WHERE clause
        
        Returns:
            bool: True if update successful, False otherwise
        """
        if not data:
            logger.warning("No data provided for update operation")
            return False
        
        try:
            set_clauses = [f"{col} = ?" for col in data.keys()]
            set_clause = ', '.join(set_clauses)
            
            query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
            
            # Combine data values with where parameters
            params = list(data.values())
            if where_params:
                params.extend(where_params)
            
            result = self.execute_query(query, tuple(params))
            if result:
                logger.info(f"Record(s) updated successfully in {table}")
            return result
        except Exception as e:
            logger.error(f"Error updating record(s) in {table}: {str(e)}")
            return False
    
    def delete_record(self, table: str, where_clause: str, where_params: Optional[Tuple] = None) -> bool:
        """
        Delete records from the specified table.
        
        Args:
            table (str): Table name
            where_clause (str): WHERE clause (without WHERE keyword)
            where_params (Optional[Tuple]): Parameters for WHERE clause
        
        Returns:
            bool: True if delete successful, False otherwise
        """
        try:
            query = f"DELETE FROM {table} WHERE {where_clause}"
            
            result = self.execute_query(query, where_params)
            if result:
                logger.info(f"Record(s) deleted successfully from {table}")
            return result
        except Exception as e:
            logger.error(f"Error deleting record(s) from {table}: {str(e)}")
            return False
    
    def get_table_info(self, table: str) -> Dict[str, Any]:
        """
        Get information about a table structure.
        
        Args:
            table (str): Table name
        
        Returns:
            Dict[str, Any]: Dictionary containing table information
        """
        if not self.connection:
            if not self.create_connection():
                return {}
        
        try:
            # Get table schema information
            schema_query = f"PRAGMA table_info({table})"
            columns_info = self.fetch_all(schema_query)
            
            # Get table row count
            count_query = f"SELECT COUNT(*) as row_count FROM {table}"
            count_result = self.fetch_one(count_query)
            row_count = count_result['row_count'] if count_result else 0
            
            # Get table indexes
            indexes_query = f"PRAGMA index_list({table})"
            indexes_info = self.fetch_all(indexes_query)
            
            table_info = {
                'table_name': table,
                'columns': columns_info,
                'row_count': row_count,
                'indexes': indexes_info
            }
            
            logger.info(f"Retrieved table information for {table}")
            return table_info
        except Exception as e:
            logger.error(f"Error getting table info for {table}: {str(e)}")
            return {}