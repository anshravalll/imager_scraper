import gradio as gr
import os

# Define the base directory structure
BASE_DIR = "Amazon\Women"

# Global variables to keep track of the current state
current_keyword_index = 0
current_title_index = 0
image_dir = None
keywords = []
titles = []

# Helper function to load keywords and titles (directories)
def load_directory_structure():
    global keywords, titles
    keywords = [f for f in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, f))]
    if keywords:
        load_titles_for_keyword()

# Helper function to load titles under the current keyword
def load_titles_for_keyword():
    global titles, current_keyword_index
    keyword_dir = os.path.join(BASE_DIR, keywords[current_keyword_index])
    titles = [f for f in os.listdir(keyword_dir) if os.path.isdir(os.path.join(keyword_dir, f))]

# Load images from the current "Images" folder
def load_images():
    global current_title_index, image_dir
    if titles:
        title_dir = os.path.join(BASE_DIR, keywords[current_keyword_index], titles[current_title_index], "Images")
        image_dir = title_dir
        image_files = [os.path.join(title_dir, img) for img in os.listdir(title_dir) if img.endswith(('.jpg', '.jpeg', '.png'))]
        return image_files
    return []

# Function to delete a selected image
def delete_image(image_path):
    if os.path.exists(image_path):
        os.remove(image_path)
    return load_images()  # Return the updated list of images after deletion

# Function to move to the next product (next title directory)
def next_product():
    global current_title_index, current_keyword_index
    current_title_index += 1
    if current_title_index >= len(titles):
        current_title_index = 0
        current_keyword_index += 1
        if current_keyword_index >= len(keywords):
            current_keyword_index = 0  # Loop back to the first keyword if all are done
        load_titles_for_keyword()
    return load_images()

# Initialize the directory structure on launch
load_directory_structure()

# Blocks context to create the Gradio app
with gr.Blocks() as app:
    # Display images
    image_gallery = gr.Gallery(label="Product Images", columns=3).style()  # Use columns instead of grid
    image_gallery.update(load_images())  # Load initial images

    # Button to delete the currently selected image
    delete_button = gr.Button("Delete Selected Image")
    image_selector = gr.Image(type="filepath", label="Select Image")  # Selector for image to delete

    # Update the image selector when an image is clicked in the gallery
    def select_image(image):
        return image  # Set the image path for the selector

    image_gallery.select(select_image, outputs=image_selector)

    delete_button.click(delete_image, inputs=image_selector, outputs=image_gallery)

    # Button to move to the next product
    next_button = gr.Button("Next Product")
    next_button.click(next_product, inputs=None, outputs=image_gallery)

# Launch the Gradio app
app.launch()
