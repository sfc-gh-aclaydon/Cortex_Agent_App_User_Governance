import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Snowflake Configuration
    SNOWFLAKE_USER = os.environ.get('SNOWFLAKE_USER')
    SNOWFLAKE_PASSWORD = os.environ.get('SNOWFLAKE_PASSWORD')
    SNOWFLAKE_ACCOUNT = os.environ.get('SNOWFLAKE_ACCOUNT')
    SNOWFLAKE_WAREHOUSE = os.environ.get('SNOWFLAKE_WAREHOUSE', 'MAPS_SEARCH_DEMO_WH')
    SNOWFLAKE_DATABASE = os.environ.get('SNOWFLAKE_DATABASE', 'MAPS_SEARCH_ANALYTICS')
    SNOWFLAKE_SCHEMA = os.environ.get('SNOWFLAKE_SCHEMA', 'APPLICATION')
    SNOWFLAKE_ROLE = os.environ.get('SNOWFLAKE_ROLE', 'SYSADMIN')
    
    # Application Configuration
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 8080))
