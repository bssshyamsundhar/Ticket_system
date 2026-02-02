import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    
    # Flask Configuration
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True') == 'True'
    
    # PostgreSQL Configuration
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
    POSTGRES_DB = os.getenv('POSTGRES_DB', 'ticketdb')
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'shyam123')
    
    @property
    def POSTGRES_URI(self):
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # SQLite Configuration (Agent Sessions)
    SQLITE_SESSION_DB = "sessions/ai_ticket_sessions.db"
    
    # ChromaDB Configuration
    CHROMA_PERSIST_DIR = "kb/chroma_db"
    CHROMA_COLLECTION_NAME = "it_support_kb"
    
    # Sentence Transformer Model
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    
    # SMTP Configuration
    SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USER = os.getenv('SMTP_USER', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    SMTP_FROM = os.getenv('SMTP_FROM', 'support@company.com')
    SMTP_ENABLED = bool(os.getenv('SMTP_USER'))  # Enable only if configured
    
    # Google Gemini API Key
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    
    # LiteLlm Configuration
    # Choose LLM provider: 'xai' for xAI Grok or 'groq' for Groq
    LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'groq')  # 'xai' or 'groq'
    
    # xAI Grok Configuration
    XAI_API_KEY = os.getenv('XAI_API_KEY', '')
    XAI_MODEL = 'xai/grok-4'
    XAI_API_BASE = 'https://api.x.ai/v1'
    
    # Groq Configuration
    GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
    GROQ_MODEL = 'groq/llama-3.3-70b-versatile'
    
    # Agent Configuration
    MAX_CLARIFICATION_ATTEMPTS = 2
    KB_CONFIDENCE_THRESHOLD = 0.7
    
    # Cloudinary Configuration
    CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME', '')
    CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY', '')
    CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET', '')
    CLOUDINARY_MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    
    # Application Settings
    APP_NAME = "IT_Support_System"

config = Config()