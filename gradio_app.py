import os
import gradio as gr
from PIL import Image

# Directory containing images
IMAGE_DIR = "C:/Users/Ansh/Desktop/coding/image_scraper/Amazon/Women/Rajasthani Lehenga Choli/Beatitude Multicolor Handwoven Kosa Silk Digital Print Designer Saree for Women Gifts Indian Saree Blouse/Images"

# Get list of images in the directory
def get_image_list(directory):
    return [os.path.join(directory, f) for f in os.listdir(directory) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

# Load image for display
def load_image(image_path):
    return Image.open(image_path)

# Delete image
def delete_image(image_path):
    try:
        os.remove(image_path)
        return f"{os.path.basename(image_path)} has been deleted."
    except Exception as e:
        return f"Error deleting {os.path.basename(image_path)}: {e}"

# Display images with thumbnails
def display_images(image_list):
    return image_list  # Return list of image paths for Gradio to handle

# Function to handle image deletion
def delete_and_refresh(selected_image, image_list):
    delete_message = delete_image(selected_image)
    updated_image_list = get_image_list(IMAGE_DIR)
    return updated_image_list, delete_message

# Create the Gradio Interface
def main():
    image_list = get_image_list(IMAGE_DIR)
    with gr.Blocks() as app:
        gr.Markdown("# Data Labeling Interface")
        gallery = gr.Gallery(label="Image Gallery", show_label=False).style(grid=2)  # Change grid for layout
        delete_button = gr.Button("Delete Selected Image")
        status_message = gr.Textbox(label="Status", interactive=False)

        # Load images into gallery
        gallery.update(value=image_list)

        # Define actions when an image is selected
        def update_on_selection(selected_image):
            if selected_image:
                delete_status = delete_and_refresh(selected_image, image_list)
                status_message.update(delete_status[1])
                gallery.update(value=delete_status[0])
            return status_message

        gallery.select(update_on_selection)
        delete_button.click(delete_and_refresh, inputs=gallery, outputs=[gallery, status_message])

    app.launch()

if __name__ == "__main__":
    main()
