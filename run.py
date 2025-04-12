from dotenv import load_dotenv
import uvicorn
import os

def main():
    # Load environment variables from .env file
    load_dotenv()
    
    # Verify required environment variables
    required_vars = [
        "FIREBASE_PROJECT_ID",
        "FIREBASE_PRIVATE_KEY_ID",
        "FIREBASE_PRIVATE_KEY",
        "FIREBASE_CLIENT_EMAIL",
        "FIREBASE_CLIENT_ID",
        "FIREBASE_CLIENT_X509_CERT_URL"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print("Error: Missing required environment variables:")
        for var in missing_vars:
            print(f"- {var}")
        print("\nPlease check your .env file")
        return
    
    # Run the application
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

if __name__ == "__main__":
    main() 