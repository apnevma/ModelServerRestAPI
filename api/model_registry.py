"""
Centralized model registry for managing available and active models.
"""
import logging
from threading import Lock
from typing import Dict, Optional, Set

logger = logging.getLogger(__name__)


class ModelRegistry:
    """
    Thread-safe registry for managing model metadata and state.
    Separates 'available' models (discovered/registered) from 'active' models (loaded and serving).
    """
    
    def __init__(self):
        self._available_models: Dict[str, dict] = {}  # model_name -> metadata
        self._active_models: Dict[str, dict] = {}     # model_name -> {model, model_info, model_path}
        self._lock = Lock()
    
    # === Available Models ===
    
    def register_model(self, model_name: str, metadata: dict) -> None:
        """Register a model as available (but not yet active)."""
        with self._lock:
            self._available_models[model_name] = metadata
            logger.info(f"[REGISTRY] Registered model '{model_name}'")
    
    def unregister_model(self, model_name: str) -> bool:
        """Remove a model from available models. Returns True if it existed."""
        with self._lock:
            if model_name in self._available_models:
                del self._available_models[model_name]
                logger.info(f"[REGISTRY] Unregistered model '{model_name}'")
                return True
            return False
    
    def get_model_metadata(self, model_name: str) -> Optional[dict]:
        """Get metadata for an available model."""
        with self._lock:
            return self._available_models.get(model_name)
    
    def list_available_models(self) -> Dict[str, dict]:
        """Get a copy of all available models."""
        with self._lock:
            return self._available_models.copy()
    
    def is_available(self, model_name: str) -> bool:
        """Check if a model is registered as available."""
        with self._lock:
            return model_name in self._available_models
    
    # === Active Models ===
    
    def activate_model(self, model_name: str, model_data: dict) -> bool:
        """
        Mark a model as active and store its runtime data.
        model_data should contain: {model, model_info, model_path}
        Returns False if model is not available.
        """
        with self._lock:
            if model_name not in self._available_models:
                logger.warning(f"[REGISTRY] Cannot activate '{model_name}': not available")
                return False
            
            self._active_models[model_name] = model_data
            logger.info(f"[REGISTRY] Activated model '{model_name}'")
            return True
    
    def deactivate_model(self, model_name: str) -> bool:
        """Remove a model from active models. Returns True if it was active."""
        with self._lock:
            if model_name in self._active_models:
                del self._active_models[model_name]
                logger.info(f"[REGISTRY] Deactivated model '{model_name}'")
                return True
            return False
    
    def get_active_model(self, model_name: str) -> Optional[dict]:
        """Get runtime data for an active model."""
        with self._lock:
            return self._active_models.get(model_name)
    
    def list_active_models(self) -> Dict[str, dict]:
        """Get a copy of all active models."""
        with self._lock:
            return self._active_models.copy()
    
    def is_active(self, model_name: str) -> bool:
        """Check if a model is currently active."""
        with self._lock:
            return model_name in self._active_models
    
    # === Utility Methods ===
    
    def get_all_model_names(self) -> Set[str]:
        """Get names of all available models (both active and inactive)."""
        with self._lock:
            return set(self._available_models.keys())
    
    def clear_all(self) -> None:
        """Clear all models (for reinitialization)."""
        with self._lock:
            self._available_models.clear()
            self._active_models.clear()
            logger.info("[REGISTRY] Cleared all models")


# Global singleton instance
_registry = ModelRegistry()


def get_registry() -> ModelRegistry:
    """Get the global model registry instance."""
    return _registry
