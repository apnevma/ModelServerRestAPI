"""
GitHub webhook event handlers.
"""
import logging
from typing import Dict, Set
from github_client import list_github_models
from model_registry import get_registry
from sync_handlers import get_sync_handler
from utils import get_model_changes

logger = logging.getLogger(__name__)


class GitHubWebhookHandler:
    """Handles GitHub webhook events for model repository changes."""
    
    def __init__(self):
        self.registry = get_registry()
        self.sync_handler = get_sync_handler()
    
    def handle_push_event(self, payload: dict, branch_filter: str = "refs/heads/main") -> None:
        """
        Process a GitHub push event.
        
        Args:
            payload: GitHub webhook payload
            branch_filter: Only process pushes to this branch (None to process all)
        """
        # Optional branch filtering
        if branch_filter and payload.get("ref") != branch_filter:
            logger.info(f"[WEBHOOK] Push ignored (branch: {payload.get('ref')})")
            return
        
        # Extract file changes from commits
        file_changes = self._get_commit_changes(payload)
        
        # Determine which changes affect models
        model_changes = get_model_changes(file_changes)
        logger.info(f"[WEBHOOK] Model changes detected: {model_changes}")
        
        # If no model changes, nothing to do
        if not any(model_changes.values()):
            logger.info("[WEBHOOK] No model-level changes detected")
            return
        
        # Process the model changes
        self._process_model_changes(model_changes)
    
    def _get_commit_changes(self, payload: dict) -> Dict[str, Set[str]]:
        """Extract file changes from all commits in the push."""
        changes = {
            "added": set(),
            "removed": set(),
            "modified": set(),
        }
        
        for commit in payload.get("commits", []):
            changes["added"].update(commit.get("added", []))
            changes["removed"].update(commit.get("removed", []))
            changes["modified"].update(commit.get("modified", []))
        
        return changes
    
    def _process_model_changes(self, model_changes: Dict[str, Set[str]]) -> None:
        """
        Process detected model changes by syncing with GitHub repository.
        
        Args:
            model_changes: dict with 'added', 'removed', 'modified' sets of model names
        """
        added = model_changes.get("added", set())
        removed = model_changes.get("removed", set())
        modified = model_changes.get("modified", set())
        
        # Handle removals first
        for model_name in removed:
            self.sync_handler.handle_model_removed(model_name)
        
        # For additions and modifications, we need fresh metadata from GitHub
        to_update = (added | modified) - removed
        
        if not to_update:
            return
        
        logger.info(f"[WEBHOOK] Refreshing metadata for {len(to_update)} model(s)")
        
        # Fetch latest model listing from GitHub
        try:
            github_entries = list_github_models()
        except Exception as e:
            logger.error(f"[WEBHOOK] Failed to list GitHub models: {e}")
            return
        
        # Update metadata for each affected model
        for model_name in to_update:
            entry = github_entries.get(model_name)
            
            if not entry:
                logger.warning(f"[WEBHOOK] Model '{model_name}' not found in GitHub listing")
                continue
            
            if model_name in added:
                self.sync_handler.handle_model_added(model_name, entry)
            elif model_name in modified:
                self.sync_handler.handle_model_modified(model_name, entry)


# Global singleton instance
_webhook_handler = None


def get_webhook_handler() -> GitHubWebhookHandler:
    """Get the global webhook handler instance."""
    global _webhook_handler
    if _webhook_handler is None:
        _webhook_handler = GitHubWebhookHandler()
    return _webhook_handler
