# Disable TensorFlow before any imports
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TRANSFORMERS_NO_TF'] = '1'
os.environ['USE_TF'] = '0'

import torch
from sentence_transformers import SentenceTransformer
from config import config
import threading
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Thread-safe lazy singleton for embedding model
_embedding_model = None
_embedding_model_lock = threading.Lock()

def get_device():
    """Get the best available device (GPU if available)"""
    if torch.cuda.is_available():
        device = 'cuda'
        gpu_name = torch.cuda.get_device_name(0)
        logger.info(f"🚀 GPU detected: {gpu_name} - Using CUDA for embeddings")
        return device
    else:
        logger.info("⚠️ No GPU detected - Using CPU for embeddings")
        return 'cpu'

def preload_embedding_model():
    """Preload embedding model with GPU support if available"""
    global _embedding_model
    with _embedding_model_lock:
        if _embedding_model is None:
            device = get_device()
            logger.info(f"Loading embedding model: {config.EMBEDDING_MODEL} on {device}")
            _embedding_model = SentenceTransformer(
                config.EMBEDDING_MODEL,
                device=device
            )
            # Warm up the model with a dummy encoding
            _ = _embedding_model.encode("warm up", show_progress_bar=False)
            logger.info(f"✅ Embedding model loaded and warmed up on {device}")

def get_embedding_model():
    """Get the embedding model (lazy load if not preloaded)"""
    global _embedding_model
    if _embedding_model is None:
        preload_embedding_model()
    return _embedding_model

