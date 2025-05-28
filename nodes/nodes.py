import json
import datetime
import numpy as np
from PIL import Image
import io
import base64
import torch
import os
import argparse

# Get ComfyUI's base directory
def get_comfyui_base_dir():
    """Get ComfyUI base directory, respecting --base-directory argument"""
    # Parse command line arguments to find base directory
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-directory', type=str, default=None)
    
    # Parse known args to avoid conflicts with other ComfyUI arguments
    try:
        known_args, _ = parser.parse_known_args()
        
        if known_args.base_directory:
            return os.path.abspath(known_args.base_directory)
    except:
        # If parsing fails, continue with fallback logic
        pass
    
    # Fallback: try to find ComfyUI directory
    # Look for ComfyUI in the current working directory or parent directories
    current_dir = os.getcwd()
    
    # Check if we're already in ComfyUI directory
    if os.path.exists(os.path.join(current_dir, 'main.py')) or \
       os.path.exists(os.path.join(current_dir, 'server.py')) or \
       os.path.exists(os.path.join(current_dir, 'nodes.py')):
        return current_dir
    
    # Look for ComfyUI in parent directories
    parent_dir = os.path.dirname(current_dir)
    while parent_dir != current_dir:
        if os.path.exists(os.path.join(parent_dir, 'main.py')) or \
           os.path.exists(os.path.join(parent_dir, 'server.py')):
            return parent_dir
        current_dir = parent_dir
        parent_dir = os.path.dirname(current_dir)
    
    # If not found, use current working directory
    return os.getcwd()

# Define a class for the custom node
class LogImageNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": { 
                "image_in": ("IMAGE", {}),
                "title": ("STRING", {"default": "image #"}),
                "description": ("STRING", {"multiline": True, "default": "image of something."}) 
            },
            "optional": {
                "custom_directory": ("STRING", {"default": ""}),
                "save_to_output": ("BOOLEAN", {"default": True}),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
                "prompt": "PROMPT", 
            }
        }

    RETURN_TYPES = ()
    OUTPUT_NODE = True
    CATEGORY = "Logger"
    FUNCTION = "loog"

    def loog(self, image_in, unique_id, prompt, title, description, custom_directory="", save_to_output=True):
        image_strings = []  # Array to hold base64 image strings

        try:
            # Check if image_in is a tensor (PyTorch)
            if isinstance(image_in, torch.Tensor):
                # Move tensor to CPU (if necessary) and convert to NumPy array
                image_in = image_in.cpu().numpy()

            # Ensure image_in is a NumPy array
            if not isinstance(image_in, np.ndarray):
                raise TypeError("image_in must be a NumPy array or a tensor.")

            # Handle different shapes
            if image_in.ndim == 4:  # Shape (batch_size, height, width, channels)
                # Process each image in the batch
                for i in range(image_in.shape[0]):
                    img_str = process_image(image_in[i])
                    if img_str:
                        image_strings.append(img_str)
            elif image_in.ndim == 3:  # Shape (height, width, channels)
                # Process single image
                img_str = process_image(image_in)
                if img_str:
                        image_strings.append(img_str)
            else:
                raise ValueError("Unsupported number of dimensions: {}".format(image_in.ndim))

        except Exception as e:
            print(f"Error processing image: {e}")

        # Get base directory
        base_dir = get_comfyui_base_dir()
        
        # Determine output directory
        if custom_directory:
            # Use custom directory (can be relative or absolute)
            if os.path.isabs(custom_directory):
                output_dir = custom_directory
            else:
                output_dir = os.path.join(base_dir, custom_directory)
        elif save_to_output:
            # Use output directory with date structure (as requested in the issue)
            current_date = datetime.datetime.now()
            date_folder = current_date.strftime("%Y-%m")
            output_dir = os.path.join(base_dir, "ComfyUI", "output", date_folder)
        else:
            # Use traditional logs directory
            output_dir = os.path.join(base_dir, "logs")
        
        # Create directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Get the current date to use in the log file name
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        log_file_name = os.path.join(output_dir, f"log_{current_date}.html")
        
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"[Log Image] Saving to: {log_file_name}")

        # Write the log entry to the dynamically named file
        with open(log_file_name, "a", encoding='utf-8') as file:
            file.write('<br><br>')
            if title:
                file.write(f"<h2>[{current_time}] {title}</h2>")
            else:
                file.write(f"<h2>[{current_time}]</h2>")
            if description:
                file.write(f"<p>{description}</p><br>")
            # Output images in HTML format if found
            file.write(f'<div style="display:flex; flex-direction: row;">')
            if image_strings:
                for img_str in image_strings:
                    file.write(f"<img style='display:block; width:100px;height:100px; padding-right: 15px;' id='base64image' src='data:image/jpeg;base64,{img_str}' />")
            file.write(f'</div>')
            file.write('<br>')
            file.write(prompt_json_to_html_table(prompt))

        return (image_in,)

def prompt_json_to_html_table(json_data):
    # Start the HTML table
    html = '<table border="1" style="border-collapse: collapse; width: 100%;">'
    html += '<tr><th style="border-left: 1px solid #ddd;background-color: #ddd;" >Node ID</th><th style="border-left: 1px solid #ddd;background-color: #ddd;">Class Type</th><th style="border-left: 1px solid #ddd;background-color: #ddd;">Inputs</th></tr>'
    
    for node_id, details in json_data.items():
        class_type = details.get('class_type', 'N/A')
        inputs = details.get('inputs', {})
        
        # Format inputs as a string for display
        inputs_str = ', '.join([f"{key}: {value}" for key, value in inputs.items()])

        # Add a row for each node
        html += f'<tr><td style="border-left: 1px solid #ddd;">{node_id}</td><td style="border-left: 1px solid #ddd;" >{class_type}</td><td style="border-left: 1px solid #ddd;">{inputs_str}</td></tr>'
    
    # End the HTML table
    html += '</table>'
    
    return html


def process_image(image):
    try:
        # Check if image needs scaling (assuming normalized values)
        if image.dtype != np.uint8:
            # Scale values to 0-255
            image = (image * 255).clip(0, 255).astype(np.uint8)

        # Convert the NumPy array to a PIL image
        if image.shape[2] == 3:  # RGB
            img = Image.fromarray(image)
        elif image.shape[2] == 4:  # RGBA
            img = Image.fromarray(image, mode='RGBA')
        else:
            raise ValueError("[Log Image] Unsupported number of channels: {}".format(image.shape[2]))

        # Create a thumbnail
        thumbnail_size = (img.width // 4, img.height // 4)  # Resize to 1/4 of original
        thumbnail = img.copy()
        thumbnail.thumbnail(thumbnail_size)

        # Convert the thumbnail to base64
        buffered = io.BytesIO()
        thumbnail.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        # Print the base64 string
        # print(f"Base64 Image : {img_str}")
        return img_str

    except Exception as e:
        print(f"[Log Image] Error processing image: {e}")
        return ''

# Node mappings for ComfyUI
NODE_CLASS_MAPPINGS = {
    "LogImageNode": LogImageNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LogImageNode": "Log Image Node"
}