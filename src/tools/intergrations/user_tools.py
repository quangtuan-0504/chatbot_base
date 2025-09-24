import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..')))
from helpers.mongodb.get_mongodb import MongoDBConnections
from bson import ObjectId
from src.utils.timezone_utils import get_gmt7_datetime_for_db
from loggers.logapp import logger
import re
import bcrypt

class UserTool:
    def __init__(self, mongodb: MongoDBConnections = None):
        self.mongodb = mongodb
        self.users_table = self.mongodb.USERS
        # Create indexes for better performance
        self.users_table.create_index([("email", 1)], unique=True)
        self.users_table.create_index([("username", 1)], unique=True)

    def _hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash using bcrypt"""
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

    def create_user(self, email: str, password: str, username: str = None, name: str = None) -> dict:
        """Create a new user"""
        # Validate email format
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValueError("Invalid email format")

        # Set default username from email if not provided
        if not username:
            username = email.split('@')[0]

        # Set default name from email if not provided
        if not name:
            name = email.split('@')[0]

        # Check if email already exists
        if self.users_table.find_one({"email": email}):
            raise ValueError("Email already registered")

        # Check if username already exists
        if self.users_table.find_one({"username": username}):
            raise ValueError("Username already taken")

        current_time = get_gmt7_datetime_for_db().isoformat()
        
        user_data = {
            "email": email,
            "username": username,
            "name": name,
            "password_hash": self._hash_password(password),
            "system_role": "user",
            "is_active": True,
            "created_at": current_time,
            "updated_at": current_time,
            "last_login": None
        }

        try:
            result = self.users_table.insert_one(user_data)
            user_id = str(result.inserted_id)
            
            # Return user data without password hash
            user_data["id"] = user_id
            del user_data["password_hash"]
            return user_data

        except Exception as e:
            logger.error(f"Failed to create user: {str(e)}")
            raise Exception(f"Failed to create user: {str(e)}")

    def authenticate_user(self, email_or_username: str, password: str) -> dict:
        """Authenticate user by email/username and password"""
        # Try to find user by email or username
        user = self.users_table.find_one({
            "$or": [
                {"email": email_or_username},
                {"username": email_or_username}
            ]
        })

        if not user:
            return None

        if not user.get("is_active"):
            return None

        if not self._verify_password(password, user["password_hash"]):
            return None

        # Convert ObjectId to string and remove password hash
        user["id"] = str(user["_id"])
        del user["_id"]
        del user["password_hash"]
        
        return user

    def get_user_by_email(self, email: str) -> dict:
        """Get user by email"""
        user = self.users_table.find_one({"email": email})
        if user:
            user["id"] = str(user["_id"])
            del user["_id"]
            if "password_hash" in user:
                del user["password_hash"]
        return user

    def get_user_by_id(self, user_id: str) -> dict:
        """Get user by ID"""
        try:
            user = self.users_table.find_one({"_id": ObjectId(user_id)})
            if user:
                user["id"] = str(user["_id"])
                del user["_id"]
                if "password_hash" in user:
                    del user["password_hash"]
            return user
        except Exception as e:
            logger.error(f"Error getting user by ID: {str(e)}")
            return None

    def update_last_login(self, user_id: str) -> bool:
        """Update user's last login timestamp"""
        try:
            current_time = get_gmt7_datetime_for_db().isoformat()
            result = self.users_table.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"last_login": current_time}}
            )
            return result.modified_count == 1
        except Exception as e:
            logger.error(f"Error updating last login: {str(e)}")
            return False

    def update_password(self, user_id: str, new_password: str) -> bool:
        """Update user password"""
        try:
            current_time = get_gmt7_datetime_for_db().isoformat()
            result = self.users_table.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "password_hash": self._hash_password(new_password),
                        "updated_at": current_time
                    }
                }
            )
            return result.modified_count == 1
        except Exception as e:
            logger.error(f"Error updating password: {str(e)}")
            return False

    def verify_password(self, email: str, password: str) -> bool:
        """Verify user password"""
        user = self.users_table.find_one({"email": email})
        if not user:
            return False
        return self._verify_password(password, user["password_hash"])

    def update_user_profile(self, user_id: str, email: str = None, name: str = None) -> dict:
        """Update user profile"""
        try:
            update_data = {"updated_at": get_gmt7_datetime_for_db().isoformat()}
            
            if email:
                # Check if email is already taken by another user
                existing_user = self.users_table.find_one({
                    "email": email,
                    "_id": {"$ne": ObjectId(user_id)}
                })
                if existing_user:
                    raise ValueError("Email already taken by another user")
                update_data["email"] = email

            if name:
                update_data["name"] = name

            result = self.users_table.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )

            if result.modified_count == 0:
                raise ValueError("User not found or no changes made")

            return self.get_user_by_id(user_id)

        except Exception as e:
            logger.error(f"Error updating user profile: {str(e)}")
            raise

    def get_all_users(self, name_filter: str = None, email_filter: str = None, page: int = 1, limit: int = 10) -> dict:
        """Get all users with optional filtering and pagination"""
        try:
            # Build filter query
            filter_query = {}
            if name_filter:
                filter_query["name"] = {"$regex": name_filter, "$options": "i"}
            if email_filter:
                filter_query["email"] = {"$regex": email_filter, "$options": "i"}

            # Calculate skip value for pagination
            skip = (page - 1) * limit

            # Get total count
            total = self.users_table.count_documents(filter_query)

            # Get users with pagination
            users_cursor = self.users_table.find(filter_query).skip(skip).limit(limit).sort("created_at", -1)
            users = []
            
            for user in users_cursor:
                user["id"] = str(user["_id"])
                del user["_id"]
                if "password_hash" in user:
                    del user["password_hash"]
                users.append(user)

            return {
                "users": users,
                "total": total
            }

        except Exception as e:
            logger.error(f"Error getting all users: {str(e)}")
            raise

    def update_user_role(self, user_id: str, system_role: str, updated_by: str) -> dict:
        """Update user system role"""
        valid_roles = ["admin", "creator", "user"]
        if system_role not in valid_roles:
            raise ValueError(f"Invalid system role. Must be one of: {valid_roles}")

        try:
            current_time = get_gmt7_datetime_for_db().isoformat()
            result = self.users_table.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "system_role": system_role,
                        "updated_at": current_time
                    }
                }
            )

            if result.modified_count == 0:
                raise ValueError("User not found or no changes made")

            logger.info(f"User {user_id} role updated to {system_role} by {updated_by}")
            return self.get_user_by_id(user_id)

        except Exception as e:
            logger.error(f"Error updating user role: {str(e)}")
            raise

    def create_admin_user(self, email: str, password: str, username: str = "admin", name: str = "Administrator") -> dict:
        """Create admin user (used during app startup)"""
        try:
            # Check if admin already exists
            existing_admin = self.users_table.find_one({"email": email})
            if existing_admin:
                logger.info("Admin user already exists")
                return existing_admin

            current_time = get_gmt7_datetime_for_db().isoformat()
            
            admin_data = {
                "email": email,
                "username": username,
                "name": name,
                "password_hash": self._hash_password(password),
                "system_role": "admin",
                "is_active": True,
                "created_at": current_time,
                "updated_at": current_time,
                "last_login": None
            }

            result = self.users_table.insert_one(admin_data)
            logger.info(f"Admin user created with ID: {result.inserted_id}")
            
            admin_data["id"] = str(result.inserted_id)
            del admin_data["password_hash"]
            return admin_data

        except Exception as e:
            logger.error(f"Failed to create admin user: {str(e)}")
            raise
