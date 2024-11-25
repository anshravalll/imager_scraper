import os
import shutil
from datetime import datetime
from collections import Counter

def process_directory(base_dir, source_dir=None, threshold_day=18, remove_duplicates=False, remove_empty_folders=False):
    """
    Processes the specified directory by removing duplicates, counting items modified before a given threshold date, 
    and optionally removing empty folders.

    Parameters:
        base_dir (str): The base directory to process.
        source_dir (str, optional): The directory containing source files for duplicate removal. Defaults to None.
        threshold_day (int, optional): The day threshold to filter items by modification date. Defaults to 18.
        remove_duplicates (bool, optional): Whether to remove duplicate files. Defaults to False.
        remove_empty_folders (bool, optional): Whether to remove empty folders. Defaults to False.

    Returns:
        dict: A summary of the operations performed, including the total items removed, counted, and directories removed.
    """
    total_removed, total_items = 0, 0
    counter = Counter({"total_removed_dirs": 0})

    # Remove duplicates
    if remove_duplicates and source_dir:
        total_removed += remove_duplicates_from_directory(base_dir, source_dir)

    # Count items modified before the threshold date
    if not remove_duplicates:
        total_items += count_items_before_threshold(base_dir, threshold_day)

    # Remove empty folders
    if remove_empty_folders:
        counter["total_removed_dirs"] += remove_empty_subdirectories(base_dir)

    # Create summary
    summary = {
        "total_removed": total_removed,
        "total_items": total_items,
        "total_removed_dirs": counter["total_removed_dirs"]
    }

    # Log summary
    log_summary(summary)

    return summary

def remove_duplicates_from_directory(base_dir, source_dir):
    """Removes duplicate files from the target directory based on the source directory."""
    total_removed = 0
    try:
        source_files = set(os.listdir(source_dir))
    except Exception as e:
        print(f"Error accessing source directory: {e}")
        return total_removed
    
    try:
        target_folders = [folder for folder in os.listdir(base_dir) if not folder.startswith('.')]
        target_folders = sorted(target_folders, key=lambda x: os.path.getmtime(os.path.join(base_dir, x)))
    except Exception as e:
        print(f"Error accessing base directory: {e}")
        return total_removed
    
    for folder in target_folders[:20]:
        folder_path = os.path.join(base_dir, folder)
        try:
            files_in_folder = os.scandir(folder_path)
        except Exception as e:
            print(f"Error accessing folder {folder}: {e}")
            continue

        count = sum(
            remove_file(file) for file in files_in_folder if file.name in source_files
        )
        total_removed += count
        print(f"Total items removed from folder '{folder}': {count}\n")
    
    return total_removed

def count_items_before_threshold(base_dir, threshold_day):
    """Counts items modified before the given threshold date."""
    total_items = 0
    current_date = datetime.now()
    for folder in os.listdir(base_dir):
        if folder.startswith('.'):
            continue  # Skip hidden folders
        folder_path = os.path.join(base_dir, folder)
        if os.path.isdir(folder_path):
            try:
                mod_date = datetime.fromtimestamp(os.path.getmtime(folder_path))
            except Exception as e:
                print(f"Error accessing modification time for {folder}: {e}")
                continue
            
            if mod_date <= current_date.replace(day=threshold_day):
                try:
                    total_items += len(os.listdir(folder_path))
                except Exception as e:
                    print(f"Error accessing folder contents for {folder}: {e}")
                    continue
    print(f"Total items modified before the threshold date: {total_items}")
    return total_items

def remove_empty_subdirectories(base_dir):
    """Removes empty subdirectories."""
    total_removed_dirs = 0
    for folder in os.listdir(base_dir):
        if folder.startswith('.'):
            continue  # Skip hidden folders
        folder_path = os.path.join(base_dir, folder)
        for subfolder in os.listdir(folder_path):
            image_dir = os.path.join(folder_path, subfolder, "Images")
            try:
                if not os.listdir(image_dir):
                    os.removedirs(image_dir)
                    total_removed_dirs += 1
                    print(f"Removing {image_dir}")
            except Exception as e:
                print(f"Error accessing or removing {image_dir}: {e}")
                continue
    print(f"Total number of removed directories: {total_removed_dirs}")
    return total_removed_dirs

def remove_file(file):
    try:
        if file.name.startswith('.'):
            print(f"Skipping hidden file or directory: {file.name}")
            return 0
        if file.is_symlink():
            print(f"Skipping symbolic link: {file.name}")
            return 0
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
