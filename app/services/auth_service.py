import firebase_admin
from firebase_admin import auth, credentials, firestore
from datetime import datetime, timedelta, UTC
from typing import Optional
from app.models.user import User, UserCreate, Token
from app.core.exceptions import AuthenticationError
from app.core.logging import logger
from app.core.firebase_config import firebase_config
import os

class AuthService:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AuthService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            try:
                # Check if Firebase is already initialized
                if not firebase_admin._apps:
                    # Initialize Firebase Admin SDK with config
                    cred = credentials.Certificate(firebase_config.get_credentials_dict())
                    firebase_admin.initialize_app(cred)
                    self.db = firestore.client()
                    logger.info("Firebase Admin SDK initialized successfully")
                else:
                    self.db = firestore.client()
                    logger.info("Using existing Firebase Admin SDK instance")
                
                self._initialized = True
            except Exception as e:
                logger.error("Failed to initialize Firebase", extra={"error": str(e)})
                raise AuthenticationError("Failed to initialize authentication service")

    def create_custom_token(self, uid: str) -> str:
        """Create a custom token for a user."""
        try:
            custom_token = auth.create_custom_token(uid)
            logger.debug("Created custom token", extra={"user_id": uid})
            return custom_token
        except Exception as e:
            logger.error("Failed to create custom token", extra={"error": str(e)})
            raise AuthenticationError("Failed to create custom token")

    async def register_user(self, user_data: UserCreate) -> tuple[User, str]:
        """
        Register a new user.
        
        Returns:
            tuple[User, str]: User object and custom token
        """
        try:
            # Create user in Firebase Auth
            firebase_user = auth.create_user(
                email=user_data.email,
                password=user_data.password,
                display_name=user_data.full_name
            )
            
            # Create user document in Firestore
            user_doc = {
                "id": firebase_user.uid,
                "email": user_data.email,
                "full_name": user_data.full_name,
                "created_at": datetime.now(UTC),
                "is_active": True,
                "current_transactions": [],
                "upload_history": []
            }
            
            self.db.collection("users").document(firebase_user.uid).set(user_doc)
            
            # Create custom token
            custom_token = auth.create_custom_token(firebase_user.uid)
            
            logger.info("User registered successfully", extra={"user_id": firebase_user.uid})
            return User(**user_doc), custom_token
            
        except Exception as e:
            logger.error("Failed to register user", extra={"error": str(e)})
            raise AuthenticationError(f"Failed to register user: {str(e)}")

    async def login_user(self, custom_token: str) -> Token:
        """Login user and return access token."""
        try:
            # For custom tokens, we'll use the token directly as the user ID
            user_id = custom_token
            
            # Verify user exists in Firestore
            user_doc = self.db.collection("users").document(user_id).get()
            if not user_doc.exists:
                logger.error("User not found in Firestore", extra={"user_id": user_id})
                raise AuthenticationError("User not found")
            
            # Create new custom token
            new_custom_token = auth.create_custom_token(user_id)
            
            logger.info("User logged in successfully", extra={"user_id": user_id})
            return Token(
                access_token=new_custom_token,
                token_type="bearer"
            )
            
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error("Failed to login user", extra={"error": str(e)})
            raise AuthenticationError("Invalid credentials")

    async def get_current_user(self, token: str) -> User:
        """Get current user from token."""
        try:
            # For custom tokens, we'll use the token directly as the user ID
            user_id = token
            
            # Get user data from Firestore
            user_doc = self.db.collection("users").document(user_id).get()
            if not user_doc.exists:
                raise AuthenticationError("User not found")
            
            logger.debug("Retrieved current user", extra={"user_id": user_id})
            return User(**user_doc.to_dict())
            
        except Exception as e:
            logger.error("Failed to get current user", extra={"error": str(e)})
            raise AuthenticationError("Invalid token")

    async def update_user_transactions(self, user_id: str, transaction_id: str, upload_data: dict):
        """Update user's transactions and upload history."""
        try:
            user_ref = self.db.collection("users").document(user_id)
            
            # Add to current transactions
            user_ref.update({
                "current_transactions": firestore.ArrayUnion([transaction_id])
            })
            
            # Add to upload history with file metadata only (not the actual file)
            upload_metadata = {
                "transaction_id": transaction_id,
                "filename": upload_data.get("filename"),
                "duration": upload_data.get("duration"),
                "sample_rate": upload_data.get("sample_rate"),
                "status": upload_data.get("status"),
                "timestamp": datetime.now(UTC)
            }
            
            user_ref.update({
                "upload_history": firestore.ArrayUnion([upload_metadata])
            })
            
            logger.debug("Updated user transactions", extra={
                "user_id": user_id,
                "transaction_id": transaction_id
            })
            
        except Exception as e:
            logger.error("Failed to update user transactions", extra={"error": str(e)})
            raise AuthenticationError("Failed to update user data") 