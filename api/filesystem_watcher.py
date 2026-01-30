"""
Filesystem monitoring for local model changes.
"""
import os
import logging
from threading import Thread
from watchdog.observers.polling import PollingObserver as Observer
from watchdog.events import FileSystemEventHandler

from api.sync_handlers import get_sync_handler

logger = logging.getLogger(__name__)


class LocalModelWatcher(FileSystemEventHandler):
    """
    Watches a local directory for model changes and syncs with the registry.
    """
    
    def __init__(self, models_path: str):
        super().__init__()
        self.models_path = models_path
        self.sync_handler = get_sync_handler()
        self.registered_models = set(os.listdir(models_path)) if os.path.exists(models_path) else set()
    
    def on_any_event(self, event):
        """Handle any filesystem event by resyncing."""
        # Ignore events on the root folder itself
        if os.path.abspath(event.src_path) == os.path.abspath(self.models_path):
            return
        
        self._resync_models()
    
    def _resync_models(self):
        """Compare current filesystem state with registered models and sync."""
        current_models = set(os.listdir(self.models_path))
        previous_models = self.registered_models
        
        # Detect added models
        added = current_models - previous_models
        for model_filename in added:
            model_path = os.path.join(self.models_path, model_filename)
            model_name = os.path.splitext(model_filename)[0]
            
            logger.info(f"[WATCHER] Detected new model: {model_name}")
            
            metadata = {
                "source": "local_filesystem",
                "model_name": model_name,
                "model_path": model_path
            }
            
            self.sync_handler.handle_model_added(model_name, metadata)
        
        # Detect removed models
        removed = previous_models - current_models
        for model_filename in removed:
            model_name = os.path.splitext(model_filename)[0]
            
            logger.info(f"[WATCHER] Detected removed model: {model_name}")
            self.sync_handler.handle_model_removed(model_name)
        
        # Update the registered models set
        self.registered_models = current_models


class FilesystemMonitor:
    """Manager for filesystem monitoring."""
    
    def __init__(self, models_path: str):
        self.models_path = models_path
        self.observer = None
        self.observer_thread = None
    
    def start(self):
        """Start monitoring the filesystem for changes."""
        if self.observer is not None:
            logger.warning("[WATCHER] Monitor already running")
            return
        
        event_handler = LocalModelWatcher(self.models_path)
        self.observer = Observer()
        self.observer.schedule(event_handler, path=self.models_path, recursive=True)
        
        self.observer_thread = Thread(target=self.observer.start, daemon=True)
        self.observer_thread.start()
        
        logger.info(f"[WATCHER] Monitoring '{self.models_path}' for model changes")
    
    def stop(self):
        """Stop monitoring."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            logger.info("[WATCHER] Filesystem monitoring stopped")


# Global singleton instance
_fs_monitor = None


def get_filesystem_monitor(models_path: str = "/models") -> FilesystemMonitor:
    """Get the global filesystem monitor instance."""
    global _fs_monitor
    if _fs_monitor is None:
        _fs_monitor = FilesystemMonitor(models_path)
    return _fs_monitor
