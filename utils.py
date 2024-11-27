def process_directory(base_dir, source_dir=None, threshold_day=18, remove_duplicates=False, remove_empty_folders=False, calculate_size=False):
    """
    Processes the specified directory by removing duplicates, counting items modified before a given threshold date, 
    and optionally removing empty folders.

    Parameters:
        base_dir (str): The base directory to process.
        source_dir (str, optional): The directory containing source files for duplicate removal. Defaults to None.
        threshold_day (int, optional): The day threshold to filter items by modification date. Defaults to 18.
        remove_duplicates (bool, optional): Whether to remove duplicate files. Defaults to False.
        remove_empty_folders (bool, optional): Whether to remove empty folders. Defaults to False.
        calculate_size (bool, optional): Whether to calculate the size of the directory. Defaults to False.

    Returns:
        dict: A summary of the operations performed, including the total items removed, counted, directories removed, and total size.
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

    # Calculate total size of the directory
    total_size = 0
    if calculate_size:
        total_size = calculate_directory_size(base_dir)

    # Create summary
    summary = {
        "total_removed": total_removed,
        "total_items": total_items,
        "total_removed_dirs": counter["total_removed_dirs"],
        "total_size": total_size
    }

    # Log summary
    log_summary(summary)

    return summary
