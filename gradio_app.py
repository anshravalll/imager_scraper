import gradio as gr
import pandas as pd
import os
import shutil
import re
from datetime import datetime, timedelta

# Define the base directory structure
BASE_DIR = "Amazon/Women"
TRASH_DIR = {}
USER_STATE = {
    "ansh": {
        "current_keyword_index": 0,
        "current_title_index": 0,
        "keywords": [],
        "titles": [],
        "current_images": [],
        "start_datetime": datetime(2024, 11, 1),
        "end_datetime": datetime.now()
    }
}

# Load function when the app starts
def on_load(request: gr.Request):
    username = str(request.username)
    if username not in USER_STATE:
        USER_STATE[username] = {
            "current_keyword_index": 0,
            "current_title_index": 0,
            "keywords": [],
            "titles": [],
            "current_images": [],
            "start_datetime": datetime(2024, 11, 1),
            "end_datetime": datetime.now()
        }
    update_trash(username)
    load_keywords(username)
    load_titles(username)

# Update user's trash directory
def update_trash(username):  
    user_trash_dir = os.path.join("Annotation profiles", username, BASE_DIR)
    if not os.path.exists(user_trash_dir):
        os.makedirs(user_trash_dir, exist_ok=True)
    TRASH_DIR[username] = user_trash_dir

# Authenticate users
def authenticate(username, password):
    user_pass_dict = {
        "ansh": "ansh",
        "hi": "hi"
    }
    return user_pass_dict.get(username) == password

# Load keywords from directories
def load_keywords(username):
    user_keywords = [
        f for f in os.listdir(BASE_DIR)
        if os.path.isdir(os.path.join(BASE_DIR, f)) and f != "Trash"
    ]
    USER_STATE[username]["keywords"] = user_keywords
    print(f"Keywords for user {username}:", user_keywords)

# Load titles based on the current keyword
def load_titles(username):
    user_state = USER_STATE[username]
    current_keyword_index = user_state["current_keyword_index"]
    keywords = user_state["keywords"]
    
    if keywords:
        keyword_dir = os.path.join(BASE_DIR, keywords[current_keyword_index])
        titles = [
            f for f in os.listdir(keyword_dir)
            if os.path.isdir(os.path.join(keyword_dir, f))
        ]
        user_state["titles"] = titles
        print(f"Titles for user {username} under keyword {keywords[current_keyword_index]}:", titles)

# Load images from the current title
def load_images(username):
    user_state = USER_STATE[username]
    current_keyword_index = user_state["current_keyword_index"]
    current_title_index = user_state["current_title_index"]
    keywords = user_state["keywords"]
    titles = user_state["titles"]
    
    if titles:
        title_dir = os.path.join(BASE_DIR, keywords[current_keyword_index], titles[current_title_index], "Images")
        if os.path.exists(title_dir):
            current_images = [
                os.path.join(title_dir, img) for img in os.listdir(title_dir)
                if img.endswith(('.jpg', '.jpeg', '.png'))
            ]
            user_state["current_images"] = current_images
            print(f"Images for user {username}:", current_images)
            return current_images
    user_state["current_images"] = []
    return []

# Update titles based on the selected keyword
def update_titles(selected_keyword, request: gr.Request):
    username = str(request.username)
    user_state = USER_STATE[username]
    keywords = user_state["keywords"]
    
    user_state["current_keyword_index"] = keywords.index(selected_keyword)
    load_titles(username)
    return gr.update(choices=user_state["titles"], value=None)

# Update the image gallery based on the selected title
def update_gallery(selected_title, request: gr.Request):
    username = str(request.username)
    user_state = USER_STATE[username]
    current_title_index = user_state["titles"].index(selected_title)
    
    user_state["current_title_index"] = current_title_index
    image_files = load_images(username)
    image_names = [os.path.basename(img) for img in image_files]
    numbered_image_names = [f"{name} ({index + 1})" for index, name in enumerate(image_names)]
    
    return image_files, gr.update(choices=numbered_image_names)

# Select/Deselect images in the gallery
def gallery_select_deselect(selected_images, evt: gr.SelectData, request: gr.Request):
    username = str(request.username)
    current_images = USER_STATE[username]["current_images"]
    
    current_selected_image_index = int(evt.index) + 1
    image_names = [f"{os.path.basename(img)} ({index + 1})" for index, img in enumerate(current_images)]
    selected_images_indices = [int(name.split('(')[-1].strip(')')) for name in selected_images]
    
    selected_images = [
        name for name in selected_images
        if int(name.split('(')[-1].strip(')')) != current_selected_image_index
    ]

    if current_selected_image_index not in selected_images_indices:
        for img in image_names:
            img_index = int(img.split('(')[-1].strip(')'))
            if img_index == current_selected_image_index:
                selected_images.append(img)
                break

    return gr.Gallery(selected_index=None), gr.update(value=selected_images)

# Create trash path for the current user
def create_trash_path(username, keyword, title):
    trash_path = os.path.join(TRASH_DIR[username], keyword, title, "Images")
    os.makedirs(trash_path, exist_ok=True)
    return trash_path

# Move selected images to Trash
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
        updated_image_names = [f"{os.path.basename(img)} ({index + 1})" for index, img in enumerate(updated_image_files)]
        return updated_image_files, gr.update(choices=updated_image_names, value=[])

    return current_images, gr.update(choices=[f"{os.path.basename(img)} ({index + 1})" for index, img in enumerate(current_images)])

# Load images from Trash
def load_trash(request: gr.Request):
    username = str(request.username)
    user_state = USER_STATE[username]
    current_keyword_index = user_state["current_keyword_index"]
    current_title_index = user_state["current_title_index"]
    keywords = user_state["keywords"]
    titles = user_state["titles"]

    keyword = keywords[current_keyword_index]
    title = titles[current_title_index]
    trash_dir = create_trash_path(username, keyword, title)

    trash_images = [img for img in os.listdir(trash_dir) if img.endswith(('.jpg', '.jpeg', '.png'))]
    return [os.path.basename(img) for img in trash_images]

# Restore images from Trash
def restore_images(selected_trash_images, request: gr.Request):
    username = str(request.username)
    user_state = USER_STATE[username]
    current_images = user_state["current_images"]
    keywords = user_state["keywords"]
    titles = user_state["titles"]
    current_keyword_index = user_state["current_keyword_index"]
    current_title_index = user_state["current_title_index"]

    current_image_uuids = {extract_uuid(os.path.basename(img), only_uuid=True) for img in current_images}

    if selected_trash_images:
        keyword = keywords[current_keyword_index]
        title = titles[current_title_index]

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

# Extract UUID from image name
def extract_uuid(image_name, only_uuid=False):
    if only_uuid:
        match = re.match(r"([a-f0-9\-]+)(?:_\d+)?(?:\.(?:jpg|jpeg|png))?(?: \(\d+\))?$", image_name)
        if match:
            return match.group(1)  # Returns only the UUID
    else:
        match = re.match(r"([a-f0-9\-]+_\d+)(?:\.(?:jpg|jpeg|png))?(?: \(\d+\))?$", image_name)
        if match:
            return match.group(1)  # Returns UUID with suffix attached
    return None

# Delete unselected images
def delete_unselected(selected_images, request: gr.Request):
    username = str(request.username)
    user_state = USER_STATE[username]
    current_images = user_state["current_images"]
    keywords = user_state["keywords"]
    titles = user_state["titles"]
    current_keyword_index = user_state["current_keyword_index"]
    current_title_index = user_state["current_title_index"]

    selected_image_names = set()
    if selected_images:
        for img in selected_images:
            img_name = extract_uuid(img, only_uuid=False)
            if img_name:
                matching_img = next((os.path.basename(img_path) for img_path in current_images if extract_uuid(os.path.basename(img_path), only_uuid=False) == img_name), None)
                if matching_img:
                    selected_image_names.add(matching_img)

    keyword = keywords[current_keyword_index]
    title = titles[current_title_index]
    trash_dir = create_trash_path(username, keyword, title)
    os.makedirs(trash_dir, exist_ok=True)

    for img_path in current_images:
        img_name = os.path.basename(img_path)
        if img_name not in selected_image_names:
            if os.path.exists(img_path):
                shutil.move(img_path, os.path.join(trash_dir, img_name))
                print(f"Moved to Trash (unselected): {img_path}")

    updated_image_files = load_images(username)
    updated_image_names = [f"{os.path.basename(img)} ({index + 1})" for index, img in enumerate(updated_image_files)]
    return updated_image_files, gr.update(choices=updated_image_names, value=[])

# Function to move to the next title and keyword
def next_title(request: gr.Request):
    username = str(request.username)
    user_state = USER_STATE[username]
    current_keyword_index = user_state["current_keyword_index"]
    current_title_index = user_state["current_title_index"]
    keywords = user_state["keywords"]
    titles = user_state["titles"]

    current_title_index += 1

    if current_title_index >= len(titles):
        current_title_index = 0
        current_keyword_index += 1

        if current_keyword_index >= len(keywords):
            current_keyword_index = 0

        load_titles(username)
        titles = user_state["titles"]

    user_state["current_keyword_index"] = current_keyword_index
    user_state["current_title_index"] = current_title_index

    selected_keyword = keywords[current_keyword_index]
    selected_title = titles[current_title_index]

    keyword_update = gr.update(value=selected_keyword)
    title_update = gr.update(choices=titles, value=selected_title)

    image_files = load_images(username)
    image_names = [os.path.basename(img) for img in image_files]
    numbered_image_names = [f"{name} ({index + 1})" for index, name in enumerate(image_names)]

    return keyword_update, title_update, image_files, gr.update(choices=numbered_image_names, value=[])

# Function to select all images
def select_all_images(request: gr.Request):
    username = str(request.username)
    current_images = USER_STATE[username]["current_images"]
    image_names = [f"{os.path.basename(img)} ({index + 1})" for index, img in enumerate(current_images)]
    return gr.update(value=image_names)

# Function to deselect all images
def deselect_all_images():
    return gr.update(value=[])

# Function to select all items in Trash
def select_all_trash(request: gr.Request):
    trash_image_names = load_trash(request)
    return gr.update(value=trash_image_names)

# Function to deselect all items in Trash
def deselect_all_trash():
    return gr.update(value=[])

# Change datetime based on user selection
def datetime_changer(request: gr.Request, evt: gr.SelectData):
    username = str(request.username)
    user_state = USER_STATE[username]
    current_time = datetime.now()
    user_state["end_datetime"] = current_time

    if str(evt.value) == "Till now":
        default_time = datetime(2024, 11, 1)
        user_state["start_datetime"] = default_time
    elif str(evt.value) == "30m":
        user_state["start_datetime"] = current_time - timedelta(minutes=30)
    elif str(evt.value) == "1h":
        user_state["start_datetime"] = current_time - timedelta(hours=1)
    elif str(evt.value) == "2h":
        user_state["start_datetime"] = current_time - timedelta(hours=2)
    elif str(evt.value) == "4h":
        user_state["start_datetime"] = current_time - timedelta(hours=4)
    elif str(evt.value) == "1d":
        user_state["start_datetime"] = current_time - timedelta(days=1)
    elif str(evt.value) == "1w":
        user_state["start_datetime"] = current_time - timedelta(days=7)

    return user_state["start_datetime"].strftime("%Y-%m-%d %H:%M:%S"), user_state["end_datetime"].strftime("%Y-%m-%d %H:%M:%S")

# Get annotated directory lengths for usernames
def get_annoted_dir_len(current_username):
    counter_list = []
    for username in os.listdir("Annotation profiles"):
        annoted_dir_counter = 0
        base_path = os.path.join("Annotation profiles", username, BASE_DIR)
        
        if not os.path.exists(base_path):
            counter_list.append(annoted_dir_counter)
            continue

        for keyword in os.listdir(base_path):
            keyword_path = os.path.join(base_path, keyword)
            mod_time = os.path.getmtime(keyword_path)
            mod_timestamp = datetime.fromtimestamp(mod_time)
            if not (USER_STATE[current_username]["start_datetime"] <= mod_timestamp <= USER_STATE[current_username]["end_datetime"]):
                continue
            
            for title in os.listdir(keyword_path):
                title_path = os.path.join(keyword_path, title)
                title_mod_time = os.path.getmtime(title_path)
                title_mod_timestamp = datetime.fromtimestamp(title_mod_time)
                if not (USER_STATE[current_username]["start_datetime"] <= title_mod_timestamp <= USER_STATE[current_username]["end_datetime"]):
                    continue
                
                full_path = os.path.join(title_path, "Images")
                if os.path.isdir(full_path) and len(os.listdir(full_path)) > 0:
                    annoted_dir_counter += 1
        
        counter_list.append(annoted_dir_counter)
    return counter_list

# Get user data for the leaderboard
def username_data_fn(request: gr.Request):
    username = str(request.username)
    username_data = pd.DataFrame({
        "username": os.listdir(os.path.join("Annotation profiles")),
        "annoted_content": get_annoted_dir_len(username)
    })
    return username_data

# Fake user data for the leaderboard
def username_data_fake_fn():
    username_data = pd.DataFrame({
        "username": os.listdir(os.path.join("Annotation profiles")),
        "annoted_content": [0 for _ in os.listdir(os.path.join("Annotation profiles"))]
    })
    return username_data

# Initial loading of keywords and titles
load_keywords("ansh")
load_titles("ansh")  

with gr.Blocks() as app:
    # First Tab: Image Workspace
    with gr.Tab("Image Workspace"):
        app.load(on_load)

        # Dropdown for selecting keyword
        keyword_dropdown = gr.Dropdown(choices=USER_STATE["ansh"]["keywords"], label="Select Keyword", value=USER_STATE["ansh"]["keywords"][0])

        # Dropdown for selecting title
        title_dropdown = gr.Dropdown(choices=USER_STATE["ansh"]["titles"], label="Select Title", interactive=True, value=USER_STATE["ansh"]["titles"][0] if USER_STATE["ansh"]["titles"] else None)

        with gr.Row():
            # Gallery for displaying images
            image_gallery = gr.Gallery(label="Product Images", show_label=True, interactive=True, allow_preview=False)

            # Column for checkboxes and buttons
            with gr.Column():
                image_checkboxes = gr.CheckboxGroup(choices=[], label="Image with Names", interactive=True)

                # Select/Deselect buttons
                select_all_button = gr.Button("Select All")
                deselect_all_button = gr.Button("Deselect All")
                keep_selected_only_button = gr.Button("Keep selected only")

        delete_button = gr.Button("Move to Trash")
        next_button = gr.Button("Next")

        # Trash section to restore deleted images
        trash_checkboxes = gr.CheckboxGroup(choices=[], label="Trash", interactive=True)
        select_all_trash_button = gr.Button("Select All Trash")
        deselect_all_trash_button = gr.Button("Deselect All Trash")
        restore_button = gr.Button("Restore Selected from Trash")

        # Update titles when keyword is selected
        keyword_dropdown.change(
            fn=update_titles,
            inputs=[keyword_dropdown],
            outputs=[title_dropdown]
        )

        # Update gallery and checkboxes when a title is selected
        title_dropdown.change(
            fn=update_gallery,
            inputs=[title_dropdown],
            outputs=[image_gallery, image_checkboxes]
        )

        # Move selected images to Trash
        delete_button.click(
            fn=move_to_trash,
            inputs=[image_checkboxes],
            outputs=[image_gallery, image_checkboxes]
        )

        # Keep selected images only
        keep_selected_only_button.click(
            fn=delete_unselected,
            inputs=[image_checkboxes],
            outputs=[image_gallery, image_checkboxes]
        )

        # Restore images from Trash
        restore_button.click(
            fn=restore_images,
            inputs=[trash_checkboxes],
            outputs=[trash_checkboxes, image_gallery, image_checkboxes]
        )

        # Navigate to next title and keyword
        next_button.click(
            fn=next_title,
            inputs=[],
            outputs=[keyword_dropdown, title_dropdown, image_gallery, image_checkboxes]
        )

        # Select/Deselect all images functionality
        select_all_button.click(
            fn=select_all_images,
            inputs=[],
            outputs=image_checkboxes
        )

        deselect_all_button.click(
            fn=deselect_all_images,
            inputs=[],
            outputs=image_checkboxes
        )

        # Select/Deselect all images in Trash
        select_all_trash_button.click(
            fn=select_all_trash,
            inputs=[],
            outputs=trash_checkboxes
        )

        deselect_all_trash_button.click(
            fn=deselect_all_trash,
            inputs=[],
            outputs=trash_checkboxes
        )

        image_gallery.select(
            fn=gallery_select_deselect,
            inputs=[image_checkboxes],
            outputs=[image_gallery, image_checkboxes]
        )

    # Second Tab: Leaderboard
    with gr.Tab("Leaderboard"):
        gr.Markdown("### Leaderboard Data ###")
        
        with gr.Row():
            base_date = datetime(2024, 11, 1).strftime("%Y-%m-%d %H:%M:%S")
            current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            start_time = gr.DateTime(base_date, label="Start time")
            end_time = gr.DateTime(current_date, label="End time")

        with gr.Row():
            duration = gr.Radio(["Till now", "30m", "1h", "2h", "4h", "1d", "1w"], value="None", label="Duration", interactive=True)

        duration.select(
            fn=datetime_changer,
            inputs=[],
            outputs=[start_time, end_time]
        )

        plot = gr.BarPlot(
            value=username_data_fake_fn,
            x="username",
            y="annoted_content",
            x_title="Username",
            y_title="Annotated dirs",
            sort="-y",
        )

        start_time.change(
            fn=username_data_fn,
            inputs=None,
            outputs=[plot]
        )

        end_time.change(
            fn=username_data_fn,
            inputs=None,
            outputs=[plot]
        )

# Launch the Gradio app
app.launch(auth=authenticate, share = True)
