import os
from pathlib import Path
import shutil
from datetime import datetime

# # Snippet for removing duplicates of one keyword directory to another keyword directory
# lehenga_dir = set(os.listdir(r"C:\Users\Ansh\Desktop\coding\image_scraper\Amazon\Women\Indian lehenga"))
#
# keyword_folders = sorted(Path(r"C:\Users\Ansh\Desktop\coding\image_scraper\Amazon\Women").iterdir(), key=os.path.getmtime)
#
# for keyword_folder in range(min(20, len(keyword_folders))):
#     count = 0
#     files = list(keyword_folders[keyword_folder].glob("*"))  
#     for simple_dir in files:
#         if simple_dir.name in lehenga_dir:
#             count += 1
#             print(f"Removing file or directory: {simple_dir}")
#
#             try:
#                 if simple_dir.is_file():
#                     os.remove(simple_dir)
#                 elif simple_dir.is_dir():
#                     shutil.rmtree(simple_dir)  
#             except PermissionError as e:
#                 print(f"PermissionError: {e} - Skipping file or directory: {simple_dir}")
#             except Exception as e:
#                 print(f"Error: {e} - Could not delete file or directory: {simple_dir}")
#
#     print(f"Total items removed from folder '{keyword_folders[keyword_folder]}': {count}\n")


#Total number of collected product details

BASE_DIR = "Amazon/Women"
total_items = 0

# Define the threshold date (the 16th of the current month)
threshold_day = 18
current_year = datetime.now().year
current_month = datetime.now().month

for each_keywrod in os.listdir(BASE_DIR):
    full_path = os.path.join(BASE_DIR, each_keywrod)  # Combine BASE_DIR with each_keywrod
    if os.path.isdir(full_path):  # Ensure that it's a directory
        # Get the last modification time of the directory
        mod_time = os.path.getmtime(full_path)
        mod_date = datetime.fromtimestamp(mod_time)  # Convert timestamp to datetime
        
        # Check if the modification date is on or after the 16th of the current month
        if mod_date.year == current_year and mod_date.month <= current_month and mod_date.day <= threshold_day:
            # Count the items in the directory
            total_items += len(os.listdir(full_path))

print(total_items)
