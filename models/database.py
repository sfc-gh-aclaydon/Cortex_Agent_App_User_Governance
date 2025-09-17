import snowflake.connector
from snowflake.connector import DictCursor
import os
from contextlib import contextmanager

class SnowflakeConnection:
    def __init__(self):
        self.connection_params = {
            'user': os.getenv('SNOWFLAKE_USER'),
            'password': os.getenv('SNOWFLAKE_PASSWORD'),
            'account': os.getenv('SNOWFLAKE_ACCOUNT'),
            'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE', 'MAPS_SEARCH_DEMO_WH'),
            'database': os.getenv('SNOWFLAKE_DATABASE', 'MAPS_SEARCH_ANALYTICS'),
            'schema': os.getenv('SNOWFLAKE_SCHEMA', 'APPLICATION'),
            'role': os.getenv('SNOWFLAKE_ROLE', 'SYSADMIN')
        }
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = snowflake.connector.connect(**self.connection_params)
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    def test_connection(self):
        """Test database connection"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT CURRENT_VERSION()")
                result = cursor.fetchone()
                return True, f"Connected to Snowflake version: {result[0]}"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
