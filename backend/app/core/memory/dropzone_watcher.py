import os
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from .ingestion_pipeline import process_file
import time

class DropzoneHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            filepath = event.src_path
            print(f"[DROPZONE] New file detected: {filepath}")
            if filepath.endswith(('.md', '.txt', '.pdf')):
                process_file(filepath)
            else:
                print(f"[DROPZONE] Ignored unsupported file type: {filepath}")

def start_watcher(directory_to_watch: str):
    print(f"[DROPZONE] Starting watcher on {directory_to_watch}")
    
    # Ensure directory exists
    Path(directory_to_watch).mkdir(parents=True, exist_ok=True)
    
    event_handler = DropzoneHandler()
    observer = Observer()
    observer.schedule(event_handler, directory_to_watch, recursive=False)
    observer.start()
    return observer

if __name__ == "__main__":
    import asyncio
    
    # testing execution
    dropzone_dir = os.path.join(os.path.dirname(__file__), "../../../data_dropzone")
    observer = start_watcher(dropzone_dir)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
