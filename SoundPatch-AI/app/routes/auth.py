from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.models.user import User, UserCreate, Token
from app.services.auth_service import AuthService
from app.dependencies.auth import get_current_user
from app.core.exceptions import AuthenticationError
from app.core.logging import logger
from pydantic import BaseModel

router = APIRouter(
    prefix="/auth",
    tags=["authentication"]
)

# Initialize auth service
try:
    auth_service = AuthService()
    logger.info("Auth service initialized successfully")
except Exception as e:
    logger.error("Failed to initialize auth service", extra={"error": str(e)})
    raise

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class LoginRequest(BaseModel):
    id_token: str

@router.post("/register", response_model=Token)
async def register(user_data: UserCreate):
    """
    Register a new user and return a custom token.
    
    Args:
        user_data: User registration data
        
    Returns:
        Token: Custom token for the registered user
        
    Raises:
        HTTPException: If registration fails
    """
    try:
        # Register user and get custom token
        user, custom_token = await auth_service.register_user(user_data)
        logger.info("User registered successfully", extra={"user_id": user.id})
        
        return Token(
            access_token=custom_token,
            token_type="bearer"
        )
        
    except Exception as e:
        logger.error("Registration failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest):
    """
    Login with Firebase ID token.
    
    Args:
        login_data: Login data containing Firebase ID token
        
    Returns:
        Token: Access token for the logged-in user
        
    Raises:
        HTTPException: If login fails
    """
    try:
        token = await auth_service.login_user(login_data.id_token)
        logger.info("User logged in successfully")
        return token
    except Exception as e:
        logger.error("Login failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current user information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: Current user information
    """
    return current_user 