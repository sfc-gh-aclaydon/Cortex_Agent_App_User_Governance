from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class User:
    """User model for authentication and authorization"""
    user_id: int
    username: str
    full_name: str
    email: str
    is_active: bool = True
    
    def to_dict(self) -> Dict:
        """Convert user to dictionary for JSON serialization"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'full_name': self.full_name,
            'email': self.email,
            'is_active': self.is_active
        }

@dataclass
class Region:
    """Region model for user access control"""
    region_id: int
    region_name: str
    region_code: str
    
    def to_dict(self) -> Dict:
        """Convert region to dictionary for JSON serialization"""
        return {
            'region_id': self.region_id,
            'region_name': self.region_name,
            'region_code': self.region_code
        }
