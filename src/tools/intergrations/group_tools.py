import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..')))
from helpers.mongodb.get_mongodb import MongoDBConnections
from bson import ObjectId
from src.utils.timezone_utils import get_gmt7_datetime_for_db
from loggers.logapp import logger
from typing import Optional, Dict, List

class GroupTool:
    def __init__(self, mongodb: MongoDBConnections = None):
        self.mongodb = mongodb
        self.groups_table = self.mongodb.GROUPS
        self.user_group_table = self.mongodb.USER_GROUP
        self.users_table = self.mongodb.USERS

        # Create indexes for better performance
        self.groups_table.create_index([("group_name", 1)])
        self.groups_table.create_index([("manager_id", 1)])
        self.groups_table.create_index([("is_hidden", 1)])
        self.user_group_table.create_index([("user_id", 1)])
        self.user_group_table.create_index([("group_id", 1)])
        self.user_group_table.create_index([("user_id", 1), ("group_id", 1)], unique=True)

    def create_group(self, group_name: str, manager_id: str, description: str = "", 
                    is_public: bool = False, is_hidden: bool = False) -> dict:
        """Create a new group"""
        # Check if group name already exists
        if self.groups_table.find_one({"group_name": group_name}):
            raise ValueError("Group name already exists")

        current_time = get_gmt7_datetime_for_db().isoformat()
        
        group_data = {
            "group_name": group_name,
            "description": description,
            "manager_id": manager_id,
            "is_public": is_public,
            "is_hidden": is_hidden,
            "num_member": 1,  # Manager is automatically a member
            "created_at": current_time,
            "updated_at": current_time
        }

        try:
            result = self.groups_table.insert_one(group_data)
            group_id = str(result.inserted_id)
            
            # Add manager as admin_gr in user_group table
            self.user_group_table.insert_one({
                "user_id": manager_id,
                "group_id": group_id,
                "role": "admin_gr",
                "assigned_by": manager_id,
                "assigned_at": current_time
            })
            
            group_data["id"] = group_id
            return group_data

        except Exception as e:
            logger.error(f"Failed to create group: {str(e)}")
            raise Exception(f"Failed to create group: {str(e)}")

    def modify_group(self, group_id: str, user_id: str, **kwargs) -> dict:
        """Modify group information (only admin_gr can modify)"""
        # Check if user is admin_gr of the group
        if not self._is_admin_gr(user_id, group_id):
            raise ValueError("Only group admin can modify group")

        current_time = get_gmt7_datetime_for_db().isoformat()
        update_data = {"updated_at": current_time}
        
        allowed_fields = ["group_name", "description", "is_public", "is_hidden"]
        for field in allowed_fields:
            if field in kwargs and kwargs[field] is not None:
                if field == "group_name":
                    # Check if new group name already exists
                    existing_group = self.groups_table.find_one({
                        "group_name": kwargs[field],
                        "_id": {"$ne": ObjectId(group_id)}
                    })
                    if existing_group:
                        raise ValueError("Group name already exists")
                update_data[field] = kwargs[field]

        try:
            result = self.groups_table.update_one(
                {"_id": ObjectId(group_id)},
                {"$set": update_data}
            )

            if result.modified_count == 0:
                raise ValueError("Group not found or no changes made")

            return self.get_group_by_id(group_id)

        except Exception as e:
            logger.error(f"Error modifying group: {str(e)}")
            raise

    def get_groups_created_by_user(self, user_id: str, group_name: Optional[str] = None) -> List[dict]:
        """Get list of groups created by user"""
        try:
            query = {"manager_id": user_id}
            if group_name:
                query["group_name"] = {"$regex": group_name, "$options": "i"}

            groups_cursor = self.groups_table.find(query).sort("created_at", -1)
            groups = []
            
            for group in groups_cursor:
                group["id"] = str(group["_id"])
                del group["_id"]
                groups.append(group)

            return groups

        except Exception as e:
            logger.error(f"Error getting groups created by user: {str(e)}")
            raise

    def get_groups_shared_with_user(self, user_id: str, group_name: Optional[str] = None) -> List[dict]:
        """Get list of groups shared with user (where user is member)"""
        try:
            # Get group IDs where user is member (not admin_gr)
            query = {
                "user_id": user_id,
                "role": "member"
            }
            if group_name:
                query["group_name"] = {"$regex": group_name, "$options": "i"}
            user_groups = self.user_group_table.find(query)
            
            group_ids = [ObjectId(ug["group_id"]) for ug in user_groups]
            
            if not group_ids:
                return []

            groups_cursor = self.groups_table.find({"_id": {"$in": group_ids}}).sort("created_at", -1)
            groups = []
            
            for group in groups_cursor:
                group["id"] = str(group["_id"])
                del group["_id"]
                groups.append(group)

            return groups

        except Exception as e:
            logger.error(f"Error getting groups shared with user: {str(e)}")
            raise

    def get_community_groups(self, group_name: Optional[str] = None) -> List[dict]:
        """Get list of public groups (is_hidden=False)"""
        try:
            query = {"is_hidden": False}
            if group_name:
                query["group_name"] = {"$regex": group_name, "$options": "i"}

            groups_cursor = self.groups_table.find(query).sort("created_at", -1)
            groups = []
            
            for group in groups_cursor:
                group["id"] = str(group["_id"])
                del group["_id"]
                groups.append(group)

            return groups

        except Exception as e:
            logger.error(f"Error getting community groups: {str(e)}")
            raise

    def get_all_groups(self, group_name_filter: str = None, num_member_filter: int = None,
                      page: int = 1, limit: int = 10) -> dict:
        """Get all groups with filtering and pagination (admin only)"""
        try:
            filter_query = {}
            if group_name_filter:
                filter_query["group_name"] = {"$regex": group_name_filter, "$options": "i"}
            if num_member_filter:
                filter_query["num_member"] = {"$gte": num_member_filter}

            skip = (page - 1) * limit
            total = self.groups_table.count_documents(filter_query)

            groups_cursor = self.groups_table.find(filter_query).skip(skip).limit(limit).sort("created_at", -1)
            groups = []
            
            for group in groups_cursor:
                group["id"] = str(group["_id"])
                del group["_id"]
                groups.append(group)

            return {
                "groups": groups,
                "total": total
            }

        except Exception as e:
            logger.error(f"Error getting all groups: {str(e)}")
            raise

    def add_member(self, group_id: str, email: str, assigned_by: str) -> dict:
        """Add member to group"""
        # Check public group
        group = self.groups_table.find_one({"_id": ObjectId(group_id)})
        if not group['is_public']:
            # Check if assigner has permission (admin_gr or member)
            if not self._can_add_member(assigned_by, group_id):
                raise ValueError("You don't have permission to add members to this group")

        # Get user by email
        user = self.users_table.find_one({"email": email})
        if not user:
            raise ValueError("User not found")

        user_id = str(user["_id"])

        # Check if user is already in group
        existing_membership = self.user_group_table.find_one({
            "user_id": user_id,
            "group_id": group_id
        })
        if existing_membership:
            raise ValueError("User is already a member of this group")

        current_time = get_gmt7_datetime_for_db().isoformat()

        try:
            # Add user to group
            self.user_group_table.insert_one({
                "user_id": user_id,
                "group_id": group_id,
                "role": "member",
                "assigned_by": assigned_by,
                "assigned_at": current_time
            })

            # Update member count
            self.groups_table.update_one(
                {"_id": ObjectId(group_id)},
                {"$inc": {"num_member": 1}, "$set": {"updated_at": current_time}}
            )

            return {"message": "Member added successfully"}

        except Exception as e:
            logger.error(f"Error adding member: {str(e)}")
            raise

    def remove_member(self, group_id: str, email: str, removed_by: str) -> dict:
        """Remove member from group (only admin_gr can remove)"""
        # Check if remover is admin_gr
        if not self._is_admin_gr(removed_by, group_id):
            raise ValueError("Only group admin can remove members")

        # Get user by email
        user = self.users_table.find_one({"email": email})
        if not user:
            raise ValueError("User not found")

        user_id = str(user["_id"])

        # Check if user is in group
        membership = self.user_group_table.find_one({
            "user_id": user_id,
            "group_id": group_id
        })
        if not membership:
            raise ValueError("User is not a member of this group")

        # Don't allow removing the group admin
        if membership["role"] == "admin_gr":
            raise ValueError("Cannot remove group admin")

        current_time = get_gmt7_datetime_for_db().isoformat()

        try:
            # Remove user from group
            self.user_group_table.delete_one({
                "user_id": user_id,
                "group_id": group_id
            })

            # Update member count
            self.groups_table.update_one(
                {"_id": ObjectId(group_id)},
                {"$inc": {"num_member": -1}, "$set": {"updated_at": current_time}}
            )

            return {"message": "Member removed successfully"}

        except Exception as e:
            logger.error(f"Error removing member: {str(e)}")
            raise

    def get_users_in_group(self, group_id: str, user_id: str) -> List[dict]:
        """Get users in group (only for members of the group)"""
        # Check if user is member of the group
        if not self._is_member_of_group(user_id, group_id):
            raise ValueError("You are not a member of this group")

        try:
            # Get all user_ids in the group
            memberships = self.user_group_table.find({"group_id": group_id})
            user_ids = [ObjectId(membership["user_id"]) for membership in memberships]

            # Get user info (only name and email)
            users_cursor = self.users_table.find(
                {"_id": {"$in": user_ids}},
                {"name": 1, "email": 1}
            )

            users = []
            for user in users_cursor:
                users.append({
                    "name": user.get("name", ""),
                    "email": user.get("email", "")
                })

            return users

        except Exception as e:
            logger.error(f"Error getting users in group: {str(e)}")
            raise

    def remove_group(self, group_id: str, user_id: str) -> dict:
        """Remove group (only admin_gr can remove)"""
        # Check if user is admin_gr
        if not self._is_admin_gr(user_id, group_id):
            raise ValueError("Only group admin can remove group")

        try:
            # Remove all user-group relationships
            self.user_group_table.delete_many({"group_id": group_id})

            # Remove group
            result = self.groups_table.delete_one({"_id": ObjectId(group_id)})

            if result.deleted_count == 0:
                raise ValueError("Group not found")

            return {"message": "Group removed successfully"}

        except Exception as e:
            logger.error(f"Error removing group: {str(e)}")
            raise

    def get_group_by_id(self, group_id: str) -> dict:
        """Get group by ID"""
        try:
            group = self.groups_table.find_one({"_id": ObjectId(group_id)})
            if group:
                group["id"] = str(group["_id"])
                del group["_id"]
            return group
        except Exception as e:
            logger.error(f"Error getting group by ID: {str(e)}")
            return None

    def _is_admin_gr(self, user_id: str, group_id: str) -> bool:
        """Check if user is admin_gr of the group"""
        membership = self.user_group_table.find_one({
            "user_id": user_id,
            "group_id": group_id,
            "role": "admin_gr"
        })
        return membership is not None

    def _can_add_member(self, user_id: str, group_id: str) -> bool:
        """Check if user can add members (admin_gr or member)"""
        membership = self.user_group_table.find_one({
            "user_id": user_id,
            "group_id": group_id,
            "role": {"$in": ["admin_gr", "member"]}
        })
        return membership is not None

    def _is_member_of_group(self, user_id: str, group_id: str) -> bool:
        """Check if user is member of the group"""
        membership = self.user_group_table.find_one({
            "user_id": user_id,
            "group_id": group_id
        })
        return membership is not None
