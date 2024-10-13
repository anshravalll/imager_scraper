import os
import gradio as gr
from PIL import Image
import shutil
from functools import lru_cache

# Configuration
ROOT_DIR = os.path.abspath("Amazon/Women")  # Replace with your actual dataset path
THUMBNAIL_SIZE = (150, 150)  # Adjust thumbnail size as needed
THUMBNAIL_DIR = os.path.join(ROOT_DIR, ".thumbnails")

# Supported image extensions
IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.bmp')

# Ensure thumbnail directory exists
os.makedirs(THUMBNAIL_DIR, exist_ok=True)

def list_directory(path):
    """
    Lists subdirectories and image files in the given path.
    """
    try:
        items = os.listdir(path)
    except Exception as e:
        return [], [], f"Error accessing {path}: {str(e)}"
    
    dirs = [item for item in items if os.path.isdir(os.path.join(path, item))]
    images = [item for item in items if item.lower().endswith(IMAGE_EXTENSIONS)]
    return sorted(dirs), sorted(images), None

def get_thumbnail(image_path):
    """
    Generates or retrieves the thumbnail for an image.
    Thumbnails are stored in a mirrored directory structure within THUMBNAIL_DIR.
    """
    relative_path = os.path.relpath(image_path, ROOT_DIR)
    thumbnail_path = os.path.join(THUMBNAIL_DIR, relative_path)
    
    if not os.path.exists(thumbnail_path):
        os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)
        try:
            with Image.open(image_path) as img:
                img.thumbnail(THUMBNAIL_SIZE)
                img.save(thumbnail_path, "JPEG")
        except Exception as e:
            return None, f"Error creating thumbnail for {image_path}: {str(e)}"
    return thumbnail_path, None

@lru_cache(maxsize=10000)
def cached_get_thumbnail(image_path):
    thumb, error = get_thumbnail(image_path)
    return thumb

def load_thumbnails(images, current_path):
    """
    Loads thumbnails for the given list of images.
    Returns a list of tuples (image_name, thumbnail_path).
    """
    thumbnails = []
    errors = []
    for img in images:
        img_path = os.path.join(current_path, img)
        thumb_path, error = get_thumbnail(img_path)
        if thumb_path:
            thumbnails.append((img, thumb_path))
        if error:
            errors.append(error)
    return thumbnails, errors

def build_breadcrumbs(current_path):
    """
    Builds Gradio buttons for breadcrumbs based on the current path.
    """
    relative_path = os.path.relpath(current_path, ROOT_DIR)
    parts = relative_path.split(os.sep) if relative_path != "." else []
    breadcrumbs = [("Root", ROOT_DIR)] + [(part, os.path.join(ROOT_DIR, *parts[:i+1])) for i, part in enumerate(parts)]
    return breadcrumbs

def navigate(path):
    """
    Navigates to the specified path and returns the updated directories, images, and breadcrumbs.
    """
    dirs, images, error = list_directory(path)
    if error:
        return None, None, None, None, error
    
    # Check if the current path contains 'images' folder and navigate into it if exists
    images_dir = os.path.join(path, 'images')
    if os.path.isdir(images_dir):
        path = images_dir
        dirs, images, error = list_directory(path)
        if error:
            return None, None, None, None, error
    
    thumbnails, thumbnail_errors = load_thumbnails(images, path)
    breadcrumbs = build_breadcrumbs(path)
    error_messages = "\n".join(thumbnail_errors) if thumbnail_errors else None
    return breadcrumbs, dirs, thumbnails, path, error_messages

def delete_images(selected_images, current_path):
    """
    Deletes the selected images from the current directory.
    Also removes their thumbnails.
    """
    if not selected_images:
        return "No images selected for deletion.", None, None, None, None
    
    error_messages = []
    for img in selected_images:
        img_path = os.path.join(current_path, img)
        thumb_path = cached_get_thumbnail(img_path)
        try:
            os.remove(img_path)
            if thumb_path and os.path.exists(thumb_path):
                os.remove(thumb_path)
        except Exception as e:
            error_messages.append(f"Error deleting {img_path}: {str(e)}")
    
    breadcrumbs, dirs, images, path, nav_error = navigate(current_path)
    if nav_error:
        error_messages.append(nav_error)
    
    if error_messages:
        return "\n".join(error_messages), breadcrumbs, dirs, images, path
    return f"Successfully deleted {len(selected_images)} image(s).", breadcrumbs, dirs, images, path

def select_directory(selected_dir, current_path):
    """
    Handles directory selection from the directory list.
    """
    new_path = os.path.join(current_path, selected_dir)
    return navigate(new_path)

def view_full_image(selected_image, current_path):
    """
    Returns the full image to display.
    """
    if not selected_image:
        return None
    img_path = os.path.join(current_path, selected_image)
    try:
        with Image.open(img_path) as img:
            return img
    except Exception as e:
        return f"Error opening image {img_path}: {str(e)}"

def refresh_view(current_path):
    """
    Refreshes the current directory view.
    """
    return navigate(current_path)

def mark_keyword_completed(current_path):
    """
    Marks the current all_searchkeyword as completed and navigates to the next one.
    This moves the all_searchkeyword folder to a 'completed' folder.
    """
    parent_path = os.path.dirname(current_path)
    keyword_name = os.path.basename(current_path)
    completed_path = os.path.join(parent_path, "completed")
    os.makedirs(completed_path, exist_ok=True)
    try:
        shutil.move(current_path, os.path.join(completed_path, keyword_name))
        # Navigate back to parent directory
        return navigate(parent_path)
    except Exception as e:
        return f"Error marking {keyword_name} as completed: {str(e)}", None, None, None, None

# Gradio Interface
with gr.Blocks() as demo:
    gr.Markdown("## 📂 Data Cleaning Dashboard")
    
    # Breadcrumbs
    breadcrumbs_display = gr.Markdown(value="Root")
    
    # Directory and Images Layout
    with gr.Row():
        # Directory List
        with gr.Column(scale=1):
            gr.Markdown("### Directories")
            dirs_list = gr.Dropdown(choices=[], label="Subdirectories", multiselect=False)
        
        # Image Gallery
        with gr.Column(scale=3):
            gr.Markdown("### Images")
            images_gallery = gr.Gallery(label="Image Thumbnails", show_label=False, elem_id="gallery", columns=5)
    
    # Actions
    with gr.Row():
        selected_images = gr.CheckboxGroup(label="Select Images to Delete")
        delete_button = gr.Button("🗑️ Delete Selected")
        refresh_button = gr.Button("🔄 Refresh")
        mark_completed_button = gr.Button("✅ Mark Keyword as Completed")
    
    # Full Image Display
    with gr.Row():
        gr.Markdown("### Selected Image")
        full_image = gr.Image(label="Full Image")
    
    # Status Message
    status = gr.Textbox(label="Status")
    
    # Hidden state to store current path
    current_path = gr.State(value=ROOT_DIR)
    
    # Define interactions
    images_gallery.select(
        lambda selected: selected, 
        inputs=images_gallery, 
        outputs=selected_images
    )
    
    delete_button.click(
        delete_images, 
        inputs=[selected_images, current_path], 
        outputs=[status, breadcrumbs_display, dirs_list, images_gallery, current_path]
    )
    
    refresh_button.click(
        refresh_view, 
        inputs=current_path, 
        outputs=[breadcrumbs_display, dirs_list, images_gallery, current_path]
    )
    
    mark_completed_button.click(
        mark_keyword_completed,
        inputs=current_path,
        outputs=[status, breadcrumbs_display, dirs_list, images_gallery, current_path]
    )

# Initialize the first view
breadcrumbs, dirs, images, path, error = navigate(ROOT_DIR)
if error:
    print(f"Error initializing the view: {error}")
else:
    # Update the UI with the initial state
    breadcrumbs_display.value = " / ".join([name for name, _ in breadcrumbs])
    dirs_list.choices = dirs
    images_gallery.update(value=images)

# Launch the app
demo.launch(share=False)
