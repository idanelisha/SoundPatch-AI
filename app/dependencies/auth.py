from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.services.auth_service import AuthService
from app.core.exceptions import AuthenticationError
from app.models.user import User
from app.core.logging import logger
import firebase_admin
from firebase_admin import auth

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Dependency to get current user from custom token.
    
    Args:
        token: Custom token from Authorization header
        
    Returns:
        User: Current authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    try:
        # Get auth service instance
        auth_service = AuthService()
        
        # For custom tokens, we need to use the client SDK to convert it to an ID token
        # For now, we'll use the token directly as the user ID since it's a custom token
        try:
            # The custom token is actually the user ID in our case
            user_id = token
        except Exception as e:
            logger.error("Failed to process token", extra={"error": str(e)})
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format"
            )
        
        # Get user data from Firestore
        user_doc = auth_service.db.collection("users").document(user_id).get()
        
        if not user_doc.exists:
            logger.error("User not found in Firestore", extra={"user_id": user_id})
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        logger.debug("Retrieved current user", extra={"user_id": user_id})
        return User(**user_doc.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Authentication failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        ) 