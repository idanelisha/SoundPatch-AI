import firebase_admin
from firebase_admin import auth, credentials
from app.core.firebase_config import firebase_config

def generate_token(email: str) -> str:
    """Generate a custom token for a user."""
    try:
        # Initialize Firebase Admin SDK with config from environment
        cred = credentials.Certificate(firebase_config.get_credentials_dict())
        firebase_admin.initialize_app(cred)
        
        # Create a test user and get their ID token
        user = auth.create_user(email=email, password='password123')
        custom_token = auth.create_custom_token(user.uid)
        
        print(f"Generated token for user: {email}")
        print(f"Token: {custom_token}")
        return custom_token
        
    except Exception as e:
        print(f"Error generating token: {str(e)}")
        raise

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python generate_token.py <email>")
        sys.exit(1)
    
    email = sys.argv[1]
    generate_token(email) 