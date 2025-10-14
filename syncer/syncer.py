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
                if os.path.isdir(dst):
                    shutil.rmtree(dst)
                    logging.info(f"[DELETED] Directory {dst} removed")
                else:
                    os.remove(dst)
                    logging.info(f"[DELETED] File {dst} removed")
        except Exception as e:
            logging.error(f"[ERROR][DELETED] Failed to remove {dst}: {e}")

    def handle_event(self, event, event_type):
        logging.info("Inside handle_event!")
        src = event.src_path
        dst = os.path.join(DST, os.path.basename(src))

        try:
            if event.is_directory:
                # If directory exists at destination, remove it first
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
                logging.info(f"[{event_type}] Directory copied {src} → {dst}")
            else:
                shutil.copy(src, dst)
                logging.info(f"[{event_type}] File copied {src} → {dst}")
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