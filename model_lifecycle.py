"""
Handles the lifecycle operations for models: activation, deactivation, and cleanup.
"""
import logging
import os
import shutil
from typing import Optional, Tuple

import model_detector
import tf_serving_manager
from github_client import download_github_model
from model_registry import get_registry

logger = logging.getLogger(__name__)


class ModelLifecycleManager:
    """Manages model lifecycle operations (load, unload, cleanup)."""
    
    def __init__(self, models_path: str = "/models"):
        self.models_path = models_path
        self.registry = get_registry()
    
    def activate_model(self, model_name: str) -> Tuple[bool, str, Optional[dict]]:
        """
        Activate a model: download (if needed), load, and register as active.
        
        Returns:
            (success, message, model_data)
        """
        # Check if model is available
        metadata = self.registry.get_model_metadata(model_name)
        if not metadata:
            return False, "Model not found in registry", None
        
        # Check if already active
        if self.registry.is_active(model_name):
            return True, "Model already active", None
        
        # Get the model path (download if from GitHub)
        try:
            model_path = self._get_model_path(metadata)
        except Exception as e:
            return False, f"Failed to obtain model: {str(e)}", None
        
        # Detect and load the model
        try:
            model_info, model = model_detector.detect(model_path)
            if model is None:
                return False, "Unsupported or invalid model", None
        except Exception as e:
            return False, f"Failed to load model: {str(e)}", None
        
        # Register as active
        model_data = {
            "model_name": model_name,
            "model": model,
            "model_info": model_info,
            "model_path": model_path
        }
        
        self.registry.activate_model(model_name, model_data)
        logger.info(f"[LIFECYCLE] Model '{model_name}' activated successfully")
        
        return True, f"Model {model_name} activated", model_data
    
    def deactivate_model(self, model_name: str) -> Tuple[bool, str]:
        """
        Deactivate a model: stop containers and remove from active registry.
        
        Returns:
            (success, message)
        """
        if not self.registry.is_active(model_name):
            return True, "Model already inactive"
        
        # Stop TF Serving container if running
        try:
            tf_serving_manager.stop_container(model_name)
            logger.info(f"[LIFECYCLE] Stopped TF Serving container for '{model_name}'")
        except Exception as e:
            logger.warning(f"[LIFECYCLE] Error stopping container for '{model_name}': {e}")
        
        # Remove from active models
        self.registry.deactivate_model(model_name)
        logger.info(f"[LIFECYCLE] Model '{model_name}' deactivated")
        
        return True, f"Model {model_name} deactivated"
    
    def remove_model_completely(self, model_name: str) -> Tuple[bool, str]:
        """
        Completely remove a model: deactivate, unregister, and delete files.
        
        Returns:
            (success, message)
        """
        # Deactivate if active
        if self.registry.is_active(model_name):
            self.deactivate_model(model_name)
        
        # Unregister from available models
        self.registry.unregister_model(model_name)
        
        # Delete local files
        self._delete_model_files(model_name)
        
        logger.info(f"[LIFECYCLE] Model '{model_name}' completely removed")
        return True, f"Model {model_name} removed completely"
    
    def _get_model_path(self, metadata: dict) -> str:
        """
        Get the model path, downloading from GitHub if necessary.
        """
        source = metadata.get("source", "local_filesystem")
        
        if source == "local_filesystem":
            return metadata["model_path"]
        elif source == "github":
            # Download from GitHub
            logger.info(f"[LIFECYCLE] Downloading model from GitHub: {metadata['model_path']}")
            return download_github_model(metadata)
        else:
            raise ValueError(f"Unknown model source: {source}")
    
    def _delete_model_files(self, model_name: str) -> None:
        """Delete model files from local storage."""
        model_path = os.path.join(self.models_path, model_name)
        
        try:
            if os.path.exists(model_path):
                if os.path.isdir(model_path):
                    shutil.rmtree(model_path)
                    logger.info(f"[LIFECYCLE] Deleted directory: {model_path}")
                else:
                    os.remove(model_path)
                    logger.info(f"[LIFECYCLE] Deleted file: {model_path}")
        except Exception as e:
            logger.error(f"[LIFECYCLE] Failed to delete {model_path}: {e}")


# Global singleton instance
_lifecycle_manager = None


def get_lifecycle_manager(models_path: str = "/models") -> ModelLifecycleManager:
    """Get the global lifecycle manager instance."""
    global _lifecycle_manager
    if _lifecycle_manager is None:
        _lifecycle_manager = ModelLifecycleManager(models_path)
    return _lifecycle_manager
