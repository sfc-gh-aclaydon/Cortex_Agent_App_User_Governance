#!/usr/bin/env python3
"""
Simple test script to validate the Analytics POC setup
Run this script to check if your environment is configured correctly
"""

import os
import sys
from dotenv import load_dotenv

def test_python_version():
    """Test Python version requirement"""
    print("🐍 Testing Python version...")
    if sys.version_info >= (3, 11):
        print(f"✅ Python version: {sys.version}")
        return True
    else:
        print(f"❌ Python version {sys.version} is too old. Requires Python 3.11+")
        return False

def test_dependencies():
    """Test required dependencies"""
    print("\n📦 Testing dependencies...")
    required_packages = [
        'flask', 'snowflake.connector', 'bcrypt', 
        'requests', 'sqlparse', 'dotenv'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    return True

def test_environment_variables():
    """Test environment variables"""
    print("\n🔧 Testing environment variables...")
    
    # Load environment variables
    load_dotenv()
    
    required_vars = [
        'SNOWFLAKE_USER', 'SNOWFLAKE_PASSWORD', 'SNOWFLAKE_ACCOUNT'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * len(value)}")  # Hide actual values
        else:
            print(f"❌ {var}: Not set")
            missing_vars.append(var)
    
    optional_vars = {
        'SNOWFLAKE_WAREHOUSE': 'COMPUTE_WH',
        'SNOWFLAKE_DATABASE': 'MAPS_SEARCH_ANALYTICS',
        'SNOWFLAKE_SCHEMA': 'APPLICATION',
        'SNOWFLAKE_ROLE': 'ACCOUNTADMIN',
        'SECRET_KEY': 'dev-secret-key'
    }
    
    for var, default in optional_vars.items():
        value = os.getenv(var, default)
        print(f"✅ {var}: {value}")
    
    if missing_vars:
        print(f"\n⚠️  Missing required variables: {', '.join(missing_vars)}")
        print("Create a .env file based on env.example")
        return False
    
    return True

def test_snowflake_connection():
    """Test Snowflake connection"""
    print("\n❄️  Testing Snowflake connection...")
    
    try:
        from models.database import SnowflakeConnection
        
        db = SnowflakeConnection()
        success, message = db.test_connection()
        
        if success:
            print(f"✅ {message}")
            return True
        else:
            print(f"❌ {message}")
            return False
    
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        return False

def test_flask_app():
    """Test Flask app initialization"""
    print("\n🌶️  Testing Flask app...")
    
    try:
        from app import app
        
        with app.test_client() as client:
            # Test health endpoint
            response = client.get('/health')
            if response.status_code in [200, 503]:  # 503 is ok if DB not ready
                print("✅ Flask app initializes correctly")
                print(f"✅ Health endpoint responds: {response.status_code}")
                return True
            else:
                print(f"❌ Health endpoint failed: {response.status_code}")
                return False
    
    except Exception as e:
        print(f"❌ Flask app failed to initialize: {str(e)}")
        return False

def test_sql_masker():
    """Test SQL masker functionality"""
    print("\n🔒 Testing SQL masker...")
    
    try:
        from services.sql_masker import SQLMasker
        
        masker = SQLMasker()
        
        # Test SQL with security predicates
        test_sql = """
        SELECT customer_name, SUM(revenue) 
        FROM sales_data 
        WHERE quarter = 'Q4 2024' 
        AND ARRAY_CONTAINS(region_id::VARIANT, PARSE_JSON(CURRENT_SESSION():accessible_regions))
        GROUP BY customer_name
        """
        
        masked_sql = masker.mask_security_predicates(test_sql)
        
        # Check that security predicates are removed
        if 'CURRENT_SESSION' not in masked_sql and 'ARRAY_CONTAINS' not in masked_sql:
            print("✅ SQL masker removes security predicates")
            
            # Check that business logic is preserved
            if "quarter = 'Q4 2024'" in masked_sql:
                print("✅ SQL masker preserves business logic")
                return True
            else:
                print("❌ SQL masker removes business logic")
                return False
        else:
            print("❌ SQL masker doesn't remove security predicates")
            return False
    
    except Exception as e:
        print(f"❌ SQL masker test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🧪 Analytics POC Setup Validation")
    print("=" * 50)
    
    tests = [
        test_python_version,
        test_dependencies, 
        test_environment_variables,
        test_snowflake_connection,
        test_flask_app,
        test_sql_masker
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test in tests:
        try:
            if test():
                passed_tests += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Your setup is ready.")
        print("\nNext steps:")
        print("1. Run the database setup script in Snowflake (setup_database.sql)")
        print("2. Upload semantic_model.yaml to Snowflake stage")
        print("3. Start the application: python app.py")
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
