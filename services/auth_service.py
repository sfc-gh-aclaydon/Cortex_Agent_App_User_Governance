import bcrypt
import os
import logging
from dotenv import load_dotenv
from models.database import SnowflakeConnection
from models.user import User, Region
from typing import Optional, List

# Configure logging
logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        # Ensure environment variables are loaded
        load_dotenv()
        self.db = SnowflakeConnection()
    
    def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Set system admin context to access USERS table during authentication
                # This is required for the initial authentication query only
                self._set_system_admin_context(cursor)
                
                cursor.execute("""
                    SELECT user_id, username, password_hash, full_name, email, is_active
                    FROM MAPS_SEARCH_ANALYTICS.APPLICATION.USERS 
                    WHERE username = %s AND is_active = TRUE
                """, (username,))
                
                user_data = cursor.fetchone()
                if user_data and self._verify_password(password, user_data[2]):
                    return User(
                        user_id=user_data[0],
                        username=user_data[1],
                        full_name=user_data[3],
                        email=user_data[4],
                        is_active=user_data[5]
                    )
                return None
        except Exception as e:
            logger.error(f"Authentication failed for user '{username}': {str(e)}")
            return None
    
    def get_user_regions(self, user_id: int) -> List[Region]:
        """Get list of regions accessible to user"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Set system admin context to access region mapping during authentication
                self._set_system_admin_context(cursor)
                
                cursor.execute("""
                    SELECT urm.region_id, r.region_name, r.region_code
                    FROM MAPS_SEARCH_ANALYTICS.APPLICATION.USER_REGION_MAPPING urm
                    JOIN MAPS_SEARCH_ANALYTICS.APPLICATION.REGIONS r ON urm.region_id = r.region_id
                    WHERE urm.user_id = %s AND r.is_active = TRUE
                """, (user_id,))
                
                regions = cursor.fetchall()
                return [Region(region_id=r[0], region_name=r[1], region_code=r[2]) 
                       for r in regions]
        except Exception as e:
            logger.error(f"Failed to fetch regions for user_id {user_id}: {str(e)}")
            return []
    
    def _set_system_admin_context(self, cursor):
        """Set system admin context for authentication queries only
        
        This is required to bypass Row Access Policies during user authentication
        and region retrieval. In production, consider using a dedicated service account.
        """
        # Use environment variable for system admin user ID, default to 1
        system_admin_id = os.getenv('SYSTEM_ADMIN_USER_ID', '1')
        cursor.execute(f"SET current_user_id = {system_admin_id}")
        cursor.execute("SET accessible_regions = '[1,2,3,4]'")  # All regions for admin
        cursor.execute("SET is_admin = true")
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def hash_password(self, password: str) -> str:
        """Hash password for storage (utility method)"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
