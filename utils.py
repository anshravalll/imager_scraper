import os
import shutil
from datetime import datetime
from collections import Counter

def process_directory(base_dir, source_dir=None, threshold_day=18, remove_duplicates=False, remove_empty_folders=False):
    total_removed = 0
    total_items = 0
    counter = Counter()

    # 1. Remove duplicates (if requested)
    if remove_duplicates and source_dir:
        source_files = set(os.listdir(source_dir))  # Get all files in source directory
        target_folders = sorted(os.listdir(base_dir), key=lambda x: os.path.getmtime(os.path.join(base_dir, x)))
        
        for folder in range(min(20, len(target_folders))):
            count = 0
            folder_path = os.path.join(base_dir, target_folders[folder])
            files_in_folder = list(os.scandir(folder_path))

            for file in files_in_folder:
                if file.name in source_files:
                    count += 1
                    print(f"Removing file or directory: {file.name}")
                    try:
                        if file.is_file():
                            os.remove(file.path)
                        elif file.is_dir():
                            shutil.rmtree(file.path)
                    except PermissionError as e:
                        print(f"PermissionError: {e} - Skipping file or directory: {file}")
                    except Exception as e:
                        print(f"Error: {e} - Could not delete file or directory: {file}")
            total_removed += count
            print(f"Total items removed from folder '{target_folders[folder]}': {count}\n")

    # 2. Count items modified after the threshold date
    if not remove_duplicates:  # If not removing duplicates, count the items
        current_year = datetime.now().year
        current_month = datetime.now().month

        for each_keyword in os.listdir(base_dir):
            full_path = os.path.join(base_dir, each_keyword)
            if os.path.isdir(full_path):  # Ensure that it's a directory
                # Get the last modification time of the directory
                mod_time = os.path.getmtime(full_path)
                mod_date = datetime.fromtimestamp(mod_time)  # Convert timestamp to datetime

                # Check if the modification date is on or after the threshold date
                if mod_date.year == current_year and mod_date.month <= current_month and mod_date.day <= threshold_day:
                    total_items += len(os.listdir(full_path))

        print(f"Total items modified before the threshold date: {total_items}")

    # 3. Remove empty folders (if requested)
    if remove_empty_folders:
        for each_keyword in os.listdir(base_dir):
            full_path = os.path.join(base_dir, each_keyword)
            for each_title in os.listdir(full_path):
                image_directory = os.path.join(full_path, each_title, "Images")
                if len(os.listdir(image_directory)) == 0:
                    os.removedirs(image_directory)
                    counter["total_removed_dirs"] += 1
                    print(f"Removing {image_directory}")
        
        print(f"Total number of removed directories: {counter['total_removed_dirs']}")

    # Return all results as a dictionary
    return {
        "total_removed": total_removed,
        "total_items": total_items,
        "total_removed_dirs": counter["total_removed_dirs"]
    }

# Example of calling the combined function
# Uncomment the line below to call the function
# result = process_directory("Amazon/Women", source_dir=r"C:\path\to\source\directory", remove_duplicates=True, remove_empty_folders=True)
# print(result)
