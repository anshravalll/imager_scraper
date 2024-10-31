import gradio as gr
import os
import shutil
import re

# Define the base directory structure
BASE_DIR = "Amazon/Women"
TRASH_DIR = {}
USER_STATE = {
    "ansh": {
        "current_keyword_index": 0,
        "current_title_index": 0,
        "keywords": [],  # To be populated with actual keywords
        "titles": [],    # Titles will load based on the current keyword
        "current_images": []
    }
}

def on_load(request: gr.Request):
    username = str(request.username)
    if username not in USER_STATE:
        USER_STATE[username] = {
            "current_keyword_index": 0,
            "current_title_index": 0,
            "keywords": [],
            "titles": [],
            "current_images": []
        }
    update_trash(username)
    load_keywords(username)
    load_titles(username)  # Load titles based on the current keyword of "ansh"oad_titles()  # Load titles for the first keyword

def update_trash(username):  
    
    # Define the user's specific trash directory path
    user_trash_dir = os.path.join(username, BASE_DIR)
    
    # Ensure the Trash directory exists for the user
    if not os.path.exists(user_trash_dir):
        os.makedirs(user_trash_dir, exist_ok=True)
    
    # Store the path in the global dictionary
    TRASH_DIR[username] = user_trash_dir
     
def authenticate(username, password):
    user_pass_dict = {
        "ansh": "ansh",
        "hi": "hi"
    }
    # Check if username exists in the dictionary and the password matches
    return user_pass_dict.get(username) == password

# Helper function to load keywords (main directories)
def load_keywords(username):
    # Load directories under BASE_DIR as keywords for the specified user
    user_keywords = [f for f in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, f)) and f != "Trash"]
    
    # Save the keywords to the user-specific state
    USER_STATE[username]["keywords"] = user_keywords
    print(f"Keywords for user {username}:", user_keywords)

# Helper function to load titles under the selected keyword
def load_titles(username):
    user_state = USER_STATE[username]
    current_keyword_index = user_state["current_keyword_index"]
    keywords = user_state["keywords"]
    
    if keywords:
        keyword_dir = os.path.join(BASE_DIR, keywords[current_keyword_index])
        titles = [f for f in os.listdir(keyword_dir) if os.path.isdir(os.path.join(keyword_dir, f))]
        user_state["titles"] = titles
        print(f"Titles for user {username} under keyword {keywords[current_keyword_index]}:", titles)

# Helper function to load images from the current "Images" folder
def load_images(username):
    user_state = USER_STATE[username]
    current_keyword_index = user_state["current_keyword_index"]
    current_title_index = user_state["current_title_index"]
    keywords = user_state["keywords"]
    titles = user_state["titles"]
    
    if titles:
        title_dir = os.path.join(BASE_DIR, keywords[current_keyword_index], titles[current_title_index], "Images")
        if os.path.exists(title_dir):
            current_images = [os.path.join(title_dir, img) for img in os.listdir(title_dir) if img.endswith(('.jpg', '.jpeg', '.png'))]
            user_state["current_images"] = current_images
            print(f"Images for user {username}:", current_images)
            return current_images
    user_state["current_images"] = []
    return []

# Function to update titles based on selected keyword
def update_titles(selected_keyword, request: gr.Request):
    username = str(request.username)
    user_state = USER_STATE[username]
    keywords = user_state["keywords"]
    titles = user_state["titles"]
    
    # Update current keyword index and load titles
    user_state["current_keyword_index"] = keywords.index(selected_keyword)
    load_titles(username)
    return gr.update(choices=user_state["titles"], value=None)

# Function to update the image gallery and checkbox based on the selected title
def update_gallery(selected_title, request: gr.Request):
    username = str(request.username)
    user_state = USER_STATE[username]
    current_title_index = user_state["titles"].index(selected_title)
    
    # Update current title index and load images
    user_state["current_title_index"] = current_title_index
    image_files = load_images(username)
    image_names = [os.path.basename(img) for img in image_files]
    numbered_image_names = [f"{name} ({index+1})" for index, name in enumerate(image_names)]
    
    return image_files, gr.update(choices=numbered_image_names)

# Function to create the Trash path with the same structure as BASE_DIR
def create_trash_path(username, keyword, title):
    # Define path in Trash that mirrors the original directory structure
    trash_path = os.path.join(username, BASE_DIR, keyword, title, "Images")
    os.makedirs(trash_path, exist_ok=True)
    return trash_path

# Function to move selected images to Trash
def move_to_trash(selected_images, request: gr.Request):
    username = str(request.username)
    user_state = USER_STATE[username]
    current_images = user_state["current_images"]
    keywords = user_state["keywords"]
    titles = user_state["titles"]
    current_keyword_index = user_state["current_keyword_index"]
    current_title_index = user_state["current_title_index"]
    
    if selected_images:
        keyword = keywords[current_keyword_index]
        title = titles[current_title_index]
        trash_path = create_trash_path(username, keyword, title)

        for img_name in list(map(lambda x: extract_uuid(x, only_uuid=False), selected_images)):
            img_path = next((img for img in current_images if extract_uuid(os.path.basename(img), only_uuid=False) == img_name), None)
            if img_path and os.path.exists(img_path):
                target_path = os.path.join(trash_path, os.path.basename(img_path))
                shutil.move(img_path, target_path)
                print(f"Moved to Trash for user {username}: {img_path}")
        
        updated_image_files = load_images(username)
        updated_image_names = [f"{os.path.basename(img)} ({index+1})" for index, img in enumerate(updated_image_files)]
        return updated_image_files, gr.update(choices=updated_image_names, value=[])

    return current_images, gr.update(choices=[f"{os.path.basename(img)} ({index+1})" for index, img in enumerate(current_images)])

# Function to load images from Trash
def load_trash(request: gr.Request):
    username = str(request.username)
    user_state = USER_STATE[username]
    
    # Get the current keyword and title for the user
    current_keyword_index = user_state["current_keyword_index"]
    current_title_index = user_state["current_title_index"]
    keywords = user_state["keywords"]
    titles = user_state["titles"]

    # Use the current keyword and title to create the appropriate Trash path
    keyword = keywords[current_keyword_index]
    title = titles[current_title_index]
    trash_dir = create_trash_path(username, keyword, title)

    # Load images from the trash directory
    trash_images = [img for img in os.listdir(trash_dir) if img.endswith(('.jpg', '.jpeg', '.png'))]
    return [os.path.basename(img) for img in trash_images]


def restore_images(selected_trash_images, request: gr.Request):
    username = str(request.username)
    user_state = USER_STATE[username]
    current_images = user_state["current_images"]
    keywords = user_state["keywords"]
    titles = user_state["titles"]
    current_keyword_index = user_state["current_keyword_index"]
    current_title_index = user_state["current_title_index"]

    current_image_uuids = {extract_uuid(os.path.basename(img), only_uuid=True) for img in current_images if extract_uuid(os.path.basename(img), only_uuid=True)}

    if selected_trash_images:
        keyword = keywords[current_keyword_index]
        title = titles[current_title_index]

        # Get the trash path using create_trash_path
        trash_dir = create_trash_path(username, keyword, title)

        for img_name in selected_trash_images:
            trash_path = os.path.join(trash_dir, img_name)
            img_uuid = extract_uuid(img_name, only_uuid=True)

            if img_uuid in current_image_uuids and os.path.exists(trash_path):
                original_folder = os.path.join(BASE_DIR, keyword, title, "Images")
                os.makedirs(original_folder, exist_ok=True)
                shutil.move(trash_path, os.path.join(original_folder, img_name))
                print(f"Restored: {trash_path}")

    updated_trash_choices = load_trash(request)
    updated_image_files, updated_image_checkboxes = update_gallery(titles[current_title_index], request)

    return (
        gr.update(choices=updated_trash_choices, value=[]),
        updated_image_files,
        updated_image_checkboxes
    )


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

def delete_unselected(selected_images, request: gr.Request):
    # Extract user-specific state variables
    username = str(request.username)
    user_state = USER_STATE[username]
    current_images = user_state["current_images"]
    keywords = user_state["keywords"]
    titles = user_state["titles"]
    current_keyword_index = user_state["current_keyword_index"]
    current_title_index = user_state["current_title_index"]

    # Extract normalized names from selected images
    selected_image_names = set()
    if selected_images:
        for img in selected_images:
            img_name = extract_uuid(img, only_uuid=False)
            if img_name:
                matching_img = next((os.path.basename(img_path) for img_path in current_images if extract_uuid(os.path.basename(img_path), only_uuid=False) == img_name), None)
                if matching_img:
                    selected_image_names.add(matching_img)

    # Set up Trash path based on current keyword and title
    keyword = keywords[current_keyword_index]
    title = titles[current_title_index]
    trash_dir = os.path.join(username, BASE_DIR, keyword, title, "Images")
    os.makedirs(trash_dir, exist_ok=True)

    # Move unselected images to Trash
    for img_path in current_images:
        img_name = os.path.basename(img_path)
        if img_name not in selected_image_names:
            if os.path.exists(img_path):
                shutil.move(img_path, os.path.join(trash_dir, img_name))
                print(f"Moved to Trash (unselected): {img_path}")

    # Reload images and update the gallery and checkboxes
    updated_image_files = load_images(username)
    updated_image_names = [f"{os.path.basename(img)} ({index+1})" for index, img in enumerate(updated_image_files)]
    return updated_image_files, gr.update(choices=updated_image_names, value=[])

# Function to move to the next title and keyword
def next_title(request: gr.Request):
    # Extract user-specific state variables
    username = str(request.username)
    user_state = USER_STATE[username]
    current_keyword_index = user_state["current_keyword_index"]
    current_title_index = user_state["current_title_index"]
    keywords = user_state["keywords"]
    titles = user_state["titles"]

    # Increment the title index
    current_title_index += 1

    # Move to next keyword if end of titles is reached
    if current_title_index >= len(titles):
        current_title_index = 0
        current_keyword_index += 1

        # Loop back to the first keyword if the end is reached
        if current_keyword_index >= len(keywords):
            current_keyword_index = 0

        # Load new titles for the new keyword
        load_titles(username)
        titles = user_state["titles"]

    # Save updated indices back to user state
    user_state["current_keyword_index"] = current_keyword_index
    user_state["current_title_index"] = current_title_index

    # Determine current keyword and title
    selected_keyword = keywords[current_keyword_index]
    selected_title = titles[current_title_index]

    # Update dropdowns for keyword and title
    keyword_update = gr.update(value=selected_keyword)
    title_update = gr.update(choices=titles, value=selected_title)

    # Update gallery and checkboxes
    image_files = load_images(username)
    image_names = [os.path.basename(img) for img in image_files]
    numbered_image_names = [f"{name} ({index+1})" for index, name in enumerate(image_names)]

    return keyword_update, title_update, image_files, gr.update(choices=numbered_image_names, value=[])

# Function to select all images
def select_all_images(request: gr.Request):
    # Extract current images for the specific user
    username = str(request.username)
    current_images = USER_STATE[username]["current_images"]
    
    # Get all current image names with indices
    image_names = [f"{os.path.basename(img)} ({index+1})" for index, img in enumerate(current_images)]
    
    # Return an update for the checkbox group to select all images
    return gr.update(value=image_names)

# Function to deselect all images
def deselect_all_images():
    # Return an update for the checkbox group to deselect all images
    return gr.update(value=[])

# Function to select all items in Trash
def select_all_trash(request: gr.Request):
    # Get all current trash image names
    trash_image_names = load_trash(request)
    # Return an update for the trash checkbox group to select all images
    return gr.update(value=trash_image_names)

# Function to deselect all items in Trash
def deselect_all_trash():
    # Return an update for the trash checkbox group to deselect all images
    return gr.update(value=[])

load_keywords("ansh")
load_titles("ansh")  # Load titles based on the current keyword of "ansh"oad_titles()  # Load titles for the first keyword

with gr.Blocks() as app:
    app.load(on_load)
    # Dropdown for selecting keyword
    keyword_dropdown = gr.Dropdown(choices=USER_STATE["ansh"]["keywords"], label="Select Keyword", value=USER_STATE["ansh"]["keywords"][0])

    # Dropdown for selecting title (initially populated with first keyword's titles)
    title_dropdown = gr.Dropdown(choices=USER_STATE["ansh"]["titles"], label="Select Title", interactive=True, value=USER_STATE["ansh"]["titles"][0] if USER_STATE["ansh"]["titles"] else None)

    with gr.Row():
        # Gallery for displaying images
        image_gallery = gr.Gallery(label="Product Images", show_label=True, interactive=True)

        # Column for checkboxes and buttons
        with gr.Column():
            # Multi-select component for image names
            image_checkboxes = gr.CheckboxGroup(choices=[], label="Image with Names", interactive=True)

            # Add the Select All and Deselect All buttons for main images
            select_all_button = gr.Button("Select All")
            deselect_all_button = gr.Button("Deselect All")

            # New button to delete unselected images
            delete_unselected_button = gr.Button("Delete Unselected Images")


    # Delete button to move selected images to Trash
    delete_button = gr.Button("Move to Trash")

    # Add the Next button
    next_button = gr.Button("Next")

    # Trash section to restore deleted images
    trash_checkboxes = gr.CheckboxGroup(choices=[], label="Trash", interactive=True)

    # Add Select All and Deselect All buttons for Trash
    select_all_trash_button = gr.Button("Select All Trash")
    deselect_all_trash_button = gr.Button("Deselect All Trash")

    # Restore button to restore selected images from Trash
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

    # Bind the Next button to the next_title function
    next_button.click(
        fn=next_title,
        inputs=[],
        outputs=[keyword_dropdown, title_dropdown, image_gallery, image_checkboxes]
    )

    # Bind the Select All button to the select_all_images function
    select_all_button.click(
        fn=select_all_images,
        inputs=[],
        outputs=image_checkboxes
    )

    # Bind the Deselect All button to the deselect_all_images function
    deselect_all_button.click(
        fn=deselect_all_images,
        inputs=[],
        outputs=image_checkboxes
    )

    # Bind the Select All Trash button to the select_all_trash function
    select_all_trash_button.click(
        fn=select_all_trash,
        inputs=[],
        outputs=trash_checkboxes
    )

    # Bind the Deselect All Trash button to the deselect_all_trash function
    deselect_all_trash_button.click(
        fn=deselect_all_trash,
        inputs=[],
        outputs=trash_checkboxes
    )
    

# Launch the Gradio app
app.launch(auth = authenticate)
