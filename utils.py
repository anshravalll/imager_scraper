import os
import shutil
from datetime import datetime
from collections import Counter

def process_directory(base_dir, source_dir=None, threshold_day=18, remove_duplicates=False, remove_empty_folders=False):
    total_removed, total_items = 0, 0
    counter = Counter({"total_removed_dirs": 0})

    # Remove duplicates
    if remove_duplicates and source_dir:
        source_files = set(os.listdir(source_dir))
        target_folders = sorted(os.listdir(base_dir), key=lambda x: os.path.getmtime(os.path.join(base_dir, x)))
        
        for folder in target_folders[:20]:
            folder_path = os.path.join(base_dir, folder)
            files_in_folder = os.scandir(folder_path)

            count = sum(
                remove_file(file) for file in files_in_folder if file.name in source_files
            )
            total_removed += count
            print(f"Total items removed from folder '{folder}': {count}\n")

    # Count items modified before the threshold date
    if not remove_duplicates:
        current_date = datetime.now()
        for folder in os.listdir(base_dir):
            folder_path = os.path.join(base_dir, folder)
            if os.path.isdir(folder_path):
                mod_date = datetime.fromtimestamp(os.path.getmtime(folder_path))
                if mod_date <= current_date.replace(day=threshold_day):
                    total_items += len(os.listdir(folder_path))
        print(f"Total items modified before the threshold date: {total_items}")

    # Remove empty folders
    if remove_empty_folders:
        for folder in os.listdir(base_dir):
            folder_path = os.path.join(base_dir, folder)
            for subfolder in os.listdir(folder_path):
                image_dir = os.path.join(folder_path, subfolder, "Images")
                if not os.listdir(image_dir):
                    os.removedirs(image_dir)
                    counter["total_removed_dirs"] += 1
                    print(f"Removing {image_dir}")
        print(f"Total number of removed directories: {counter['total_removed_dirs']}")

    # Create summary
    summary = {
        "total_removed": total_removed,
        "total_items": total_items,
        "total_removed_dirs": counter["total_removed_dirs"]
    }

    # Log summary
    log_summary(summary)

    return summary

def remove_file(file):
    try:
        if file.is_file():
            os.remove(file.path)
        elif file.is_dir():
            shutil.rmtree(file.path)
        print(f"Removing file or directory: {file.name}")
        return 1
    except Exception as e:
        print(f"Error: {e} - Skipping file or directory: {file.name}")
        return 0

def log_summary(summary):
    """Logs the summary of operations performed."""
    print("\n--- Operation Summary ---")
    print(f"Total items removed: {summary['total_removed']}")
    print(f"Total items counted before threshold date: {summary['total_items']}")
    print(f"Total directories removed: {summary['total_removed_dirs']}")
    print("--- End of Summary ---\n")

# Example of calling the function
# result = process_directory("Amazon/Women", source_dir=r"C:\path\to\source\directory", remove_duplicates=True, remove_empty_folders=True)
# print(result)
