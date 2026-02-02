# Disable TensorFlow before any imports
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TRANSFORMERS_NO_TF'] = '1'
os.environ['USE_TF'] = '0'

from sentence_transformers import SentenceTransformer
from config import config
import threading

# Thread-safe lazy singleton for embedding model
_embedding_model = None
_embedding_model_lock = threading.Lock()

def preload_embedding_model():
    global _embedding_model
    with _embedding_model_lock:
        if _embedding_model is None:
            _embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        preload_embedding_model()
    return _embedding_model
