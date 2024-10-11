import os
from pathlib import Path
import shutil

lehenga_dir = set(os.listdir(r"C:\Users\Ansh\Desktop\coding\image_scraper\Amazon\Women\Indian lehenga"))

keyword_folders = sorted(Path(r"C:\Users\Ansh\Desktop\coding\image_scraper\Amazon\Women").iterdir(), key=os.path.getmtime)

for keyword_folder in range(min(20, len(keyword_folders))):
    count = 0
    files = list(keyword_folders[keyword_folder].glob("*"))  
    for simple_dir in files:
        if simple_dir.name in lehenga_dir:
            count += 1
            print(f"Removing file or directory: {simple_dir}")
            
            try:
                if simple_dir.is_file():
                    os.remove(simple_dir)
                elif simple_dir.is_dir():
                    shutil.rmtree(simple_dir)  
            except PermissionError as e:
                print(f"PermissionError: {e} - Skipping file or directory: {simple_dir}")
            except Exception as e:
                print(f"Error: {e} - Could not delete file or directory: {simple_dir}")

    print(f"Total items removed from folder '{keyword_folders[keyword_folder]}': {count}\n")
