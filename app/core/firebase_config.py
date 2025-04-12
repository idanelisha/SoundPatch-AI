from pydantic_settings import BaseSettings
import os

class FirebaseConfig(BaseSettings):
    # Firebase Configuration
    type: str = os.getenv("FIREBASE_TYPE", "service_account")
    project_id: str = os.getenv("FIREBASE_PROJECT_ID")
    private_key_id: str = os.getenv("FIREBASE_PRIVATE_KEY_ID")
    private_key: str = os.getenv("FIREBASE_PRIVATE_KEY")
    client_email: str = os.getenv("FIREBASE_CLIENT_EMAIL")
    client_id: str = os.getenv("FIREBASE_CLIENT_ID")
    auth_uri: str = os.getenv("FIREBASE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth")
    token_uri: str = os.getenv("FIREBASE_TOKEN_URI", "https://oauth2.googleapis.com/token")
    auth_provider_x509_cert_url: str = os.getenv("FIREBASE_AUTH_PROVIDER_X509_CERT_URL", "https://www.googleapis.com/oauth2/v1/certs")
    client_x509_cert_url: str = os.getenv("FIREBASE_CLIENT_X509_CERT_URL")

    def get_credentials_dict(self) -> dict:
        """Get the credentials dictionary for Firebase Admin SDK."""
        # Handle private key newlines properly
        private_key = self.private_key.replace('\\n', '\n') if self.private_key else None
        
        return {
            "type": self.type,
            "project_id": self.project_id,
            "private_key_id": self.private_key_id,
            "private_key": private_key,
            "client_email": self.client_email,
            "client_id": self.client_id,
            "auth_uri": self.auth_uri,
            "token_uri": self.token_uri,
            "auth_provider_x509_cert_url": self.auth_provider_x509_cert_url,
            "client_x509_cert_url": self.client_x509_cert_url
        }

    class Config:
        env_prefix = "FIREBASE_"

# Create a global instance
firebase_config = FirebaseConfig() 