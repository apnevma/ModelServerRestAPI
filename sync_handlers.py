"""
Unified handlers for model synchronization from different sources.
These functions handle the common logic for adding, removing, and updating models
regardless of whether the change comes from filesystem, GitHub, or API.
"""
import logging
from typing import Set, Dict
from model_registry import get_registry
from model_lifecycle import get_lifecycle_manager

logger = logging.getLogger(__name__)


class ModelSyncHandler:
    """Handles synchronization of models from various sources."""
    
    def __init__(self):
        self.registry = get_registry()
        self.lifecycle = get_lifecycle_manager()
    
    def handle_model_added(self, model_name: str, metadata: dict) -> None:
        """
        Handle a newly discovered model (from any source).
        Registers it as available but does not activate it.
        """
        logger.info(f"[SYNC] Model added: {model_name}")
        self.registry.register_model(model_name, metadata)
    
    def handle_model_removed(self, model_name: str) -> None:
        """
        Handle a model removal (from any source).
        Deactivates and completely removes the model.
        """
        logger.info(f"[SYNC] Model removed: {model_name}")
        self.lifecycle.remove_model_completely(model_name)
    
    def handle_model_modified(self, model_name: str, new_metadata: dict) -> None:
        """
        Handle a model update (from any source).
        Updates metadata and deactivates if currently active (requires manual reactivation).
        """
        logger.info(f"[SYNC] Model modified: {model_name}")
        
        # If the model is active, deactivate it (user must reactivate to get new version)
        if self.registry.is_active(model_name):
            logger.info(f"[SYNC] Deactivating modified model '{model_name}'")
            self.lifecycle.deactivate_model(model_name)
        
        # Update metadata
        self.registry.register_model(model_name, new_metadata)
    
    def handle_bulk_changes(self, changes: Dict[str, Set[str]]) -> None:
        """
        Handle multiple model changes at once.
        
        Args:
            changes: dict with keys 'added', 'removed', 'modified'
                    each containing a set of model names
        """
        added = changes.get("added", set())
        removed = changes.get("removed", set())
        modified = changes.get("modified", set())
        
        logger.info(f"[SYNC] Processing bulk changes - "
                   f"added: {len(added)}, removed: {len(removed)}, modified: {len(modified)}")
        
        # Process removals first
        for model_name in removed:
            self.handle_model_removed(model_name)
        
        # Then additions (with metadata to be provided by caller)
        for model_name in added:
            logger.info(f"[SYNC] Bulk add detected for '{model_name}' (metadata update needed)")
        
        # Then modifications (with metadata to be provided by caller)
        for model_name in modified:
            logger.info(f"[SYNC] Bulk modify detected for '{model_name}' (metadata update needed)")


# Global singleton instance
_sync_handler = None


def get_sync_handler() -> ModelSyncHandler:
    """Get the global sync handler instance."""
    global _sync_handler
    if _sync_handler is None:
        _sync_handler = ModelSyncHandler()
    return _sync_handler
