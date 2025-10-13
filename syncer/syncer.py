import os
import shutil
import time
import logging
from watchdog.observers.polling import PollingObserver as Observer
from watchdog.events import FileSystemEventHandler

SRC = "/local_models"
DST = "/models"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class SyncHandler(FileSystemEventHandler):
    def on_created(self, event):
        logging.info("Inside on_created!")
        self.handle_event(event, "CREATED")

    def on_modified(self, event):
        logging.info("Inside on_modified!")
        self.handle_event(event, "MODIFIED")

    def on_deleted(self, event):
        dst = os.path.join(DST, os.path.basename(event.src_path))
        try:
            if os.path.exists(dst):
                os.remove(dst)
                logging.info(f"[DELETED] {dst} removed")
        except Exception as e:
            logging.error(f"[ERROR][DELETED] Failed to remove {dst}: {e}")

    def handle_event(self, event, event_type):
        logging.info("Inside handle_event!")
        if event.is_directory:
            return
        src = event.src_path
        dst = os.path.join(DST, os.path.basename(src))
        try:
            shutil.copy(src, dst)
            logging.info(f"[{event_type}] Copied {src} → {dst}")
        except Exception as e:
            logging.error(f"[{event_type}] Failed to copy {src} → {dst}: {e}")

if __name__ == "__main__":
    logging.info(f"Watching for new models in {SRC} ...")
    event_handler = SyncHandler()
    observer = Observer()
    observer.schedule(event_handler, SRC, recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Stopping syncer...")
        observer.stop()
    observer.join()