import gradio as gr
import os
import shutil
import re

# Define the base directory structure
BASE_DIR = "Amazon/Women"
TRASH_DIR = "Amazon/Women/Trash"  # Define a folder for deleted images

# Ensure the Trash directory exists
if not os.path.exists(TRASH_DIR):
    os.makedirs(TRASH_DIR)

# Global variables to keep track of the current state
current_keyword_index = 0
current_title_index = 0
keywords = []
titles = []
current_images = []  # This will hold the currently displayed images

# Helper function to load keywords (main directories)
def load_keywords():
    global keywords
    keywords = [f for f in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, f)) and f != "Trash"]
    print("Keywords:", keywords)

# Helper function to load titles under the selected keyword
def load_titles():
    global titles, current_keyword_index
    if keywords:
        keyword_dir = os.path.join(BASE_DIR, keywords[current_keyword_index])
        titles = [f for f in os.listdir(keyword_dir) if os.path.isdir(os.path.join(keyword_dir, f))]
        print("Titles for keyword", keywords[current_keyword_index], ":", titles)

# Helper function to load images from the current "Images" folder
def load_images():
    global current_title_index, current_images
    if titles:
        title_dir = os.path.join(BASE_DIR, keywords[current_keyword_index], titles[current_title_index], "Images")
        if os.path.exists(title_dir):
            current_images = [os.path.join(title_dir, img) for img in os.listdir(title_dir) if img.endswith(('.jpg', '.jpeg', '.png'))]
            print("Images found:", current_images)
            return current_images
    return []

# Function to update titles based on selected keyword
def update_titles(selected_keyword):
    global current_keyword_index
    current_keyword_index = keywords.index(selected_keyword)  # Update the current keyword index
    load_titles()
    return gr.update(choices=titles, value=None)

# Function to update the image gallery and checkbox based on the selected title
def update_gallery(selected_title):
    global current_title_index
    current_title_index = titles.index(selected_title)  # Update the current title index
    image_files = load_images()  # Load images based on the current state
    image_names = [os.path.basename(img) for img in image_files]  # Extract names of images
    numbered_image_names = [f"{name} ({index+1})" for index, name in enumerate(image_names)]
    return image_files, gr.update(choices=numbered_image_names)

# Function to move selected images to Trash
def move_to_trash(selected_images):
    global current_images
    if selected_images:
        for img_name in list(map(extract_uuid, selected_images)):
            img_path = next((img for img in current_images if os.path.splitext(os.path.basename(img))[0] == img_name), None)
            if img_path and os.path.exists(img_path):
                trash_path = os.path.join(TRASH_DIR, os.path.basename(img_path))
                shutil.move(img_path, trash_path)
                print(f"Moved to Trash: {img_path}")
        
        # Reload the images and update the gallery and checkboxes
        updated_image_files = load_images()
        updated_image_names = [f"{os.path.basename(img)} ({index+1})" for index, img in enumerate(updated_image_files)]
        return updated_image_files, gr.update(choices=updated_image_names, value=[])

    return current_images, gr.update(choices=[f"{os.path.basename(img)} ({index+1})" for index, img in enumerate(current_images)])

# Function to load images from Trash
def load_trash():
    trash_images = [os.path.join(TRASH_DIR, img) for img in os.listdir(TRASH_DIR) if img.endswith(('.jpg', '.jpeg', '.png'))]
    return [os.path.basename(img) for img in trash_images]

# Function to extract UUID prefix from a given image name
def extract_uuid(image_name, only_uuid=False):
    """
    Extracts the UUID prefix from a given image name.
    
    Parameters:
        image_name (str): The name of the image file.
        only_uuid (bool): If True, extract only the UUID without the suffix.
                          If False, extract the UUID with the suffix.
    
    Returns:
        str: The extracted UUID or UUID with suffix, or None if no match.
    """
    if only_uuid:
        # Pattern to capture only the UUID part without the suffix
        match = re.match(r"([a-f0-9\-]+)(?:_\d+)?(?:\.(?:jpg|jpeg|png))?(?: \(\d+\))?$", image_name)
        if match:
            return match.group(1)  # Returns only the UUID
    else:
        # Pattern to capture UUID with suffix (_1, _2, etc.)
        match = re.match(r"([a-f0-9\-]+_\d+)(?:\.(?:jpg|jpeg|png))?(?: \(\d+\))?$", image_name)
        if match:
            return match.group(1)  # Returns UUID with suffix attached
    
    return None

# Function to restore selected images from Trash to the original folder
def restore_images(selected_trash_images):
    # Get UUID prefixes from currently displayed images
    current_image_uuids = {extract_uuid(os.path.basename(img), only_uuid = True) for img in current_images if extract_uuid(os.path.basename(img), only_uuid= True)}
    
    if selected_trash_images:
        for img_name in selected_trash_images:
            trash_path = os.path.join(TRASH_DIR, img_name)
            img_uuid = extract_uuid(img_name, only_uuid= True)
            
            # Only restore if the image's UUID matches those in the current folder
            if img_uuid in current_image_uuids and os.path.exists(trash_path):
                # Move back to the appropriate "Images" folder
                original_folder = os.path.join(BASE_DIR, keywords[current_keyword_index], titles[current_title_index], "Images")
                if not os.path.exists(original_folder):
                    os.makedirs(original_folder)
                shutil.move(trash_path, os.path.join(original_folder, img_name))
                print(f"Restored: {trash_path}")

    # Refresh Trash and current images
    updated_trash_choices = load_trash()
    updated_image_files, updated_image_checkboxes = update_gallery(titles[current_title_index])
    
    return (
        gr.update(choices=updated_trash_choices, value=[]),  # Clear selected items in Trash
        updated_image_files,  # Update Gallery
        updated_image_checkboxes  # Update Checkboxes in the main directory
    )

# Function to delete files other than the selected ones
def delete_unselected(selected_images):
    global current_images
    # Get the list of image names that should NOT be deleted
    selected_image_names = set(selected_images) if selected_images else set()
    
    for img_path in current_images:
        img_name = os.path.basename(img_path)
        if img_name not in selected_image_names:
            if os.path.exists(img_path):
                trash_path = os.path.join(TRASH_DIR, img_name)
                shutil.move(img_path, trash_path)
                print(f"Moved to Trash (unselected): {img_path}")
    
    # Reload the images and update the gallery and checkboxes
    updated_image_files = load_images()
    updated_image_names = [os.path.basename(img) for img in updated_image_files]
    return updated_image_files, gr.update(choices=updated_image_names, value=[])

# Initialize the directory structure by loading keywords
load_keywords()
load_titles()  # Load titles for the first keyword

with gr.Blocks() as app:
    # Dropdown for selecting keyword
    keyword_dropdown = gr.Dropdown(choices=keywords, label="Select Keyword", value=keywords[0])

    # Dropdown for selecting title (initially populated with first keyword's titles)
    title_dropdown = gr.Dropdown(choices=titles, label="Select Title", interactive=True)

    with gr.Row():
        # Gallery for displaying images
        image_gallery = gr.Gallery(label="Product Images", show_label=True, interactive=True)

        # Multi-select component for image names
        image_checkboxes = gr.CheckboxGroup(choices=[], label="Image with Names", interactive=True)

    # Delete button to move selected images to Trash
    delete_button = gr.Button("Move to Trash")

    # New button to delete unselected images
    delete_unselected_button = gr.Button("Delete Unselected Images")

    # Trash section to restore deleted images
    trash_checkboxes = gr.CheckboxGroup(choices=load_trash(), label="Trash", interactive=True)
    restore_button = gr.Button("Restore Selected from Trash")

    # Update titles when keyword is selected
    keyword_dropdown.change(
        fn=update_titles, 
        inputs=[keyword_dropdown], 
        outputs=[title_dropdown]
    )

    # Update the gallery and checkbox group when a title is selected
    title_dropdown.change(
        fn=update_gallery, 
        inputs=[title_dropdown], 
        outputs=[image_gallery, image_checkboxes]
    )

    # Move selected images to Trash when delete button is clicked
    delete_button.click(
        fn=move_to_trash, 
        inputs=[image_checkboxes], 
        outputs=[image_gallery, image_checkboxes]
    )

    # Delete unselected images when delete_unselected_button is clicked
    delete_unselected_button.click(
        fn=delete_unselected, 
        inputs=[image_checkboxes], 
        outputs=[image_gallery, image_checkboxes]
    )

    # Restore images from Trash when restore button is clicked
    restore_button.click(
        fn=restore_images, 
        inputs=[trash_checkboxes], 
        outputs=[trash_checkboxes, image_gallery, image_checkboxes]
    )

# Launch the Gradio app
app.launch()
