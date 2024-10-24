import json
import datetime
import numpy as np
from PIL import Image
import io
import base64
import torch

# Define a class for the custom node
class LogImageNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": { "image_in": ("IMAGE", {}),
             "title": ("STRING", {"default": "image #"}),
             "description": ("STRING", {"multiline": True, "default": "image of somthing."}) },
            "hidden": {
                "unique_id": "UNIQUE_ID",
                "prompt": "PROMPT", 
            }
        }

    RETURN_TYPES = ()
    OUTPUT_NODE = True
    CATEGORY = "Logger"
    FUNCTION = "loog"

    def loog(self, image_in, unique_id, prompt, title, description):
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

        # Get the current date to use in the log file name
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        log_file_name = f"logs/log_{current_date}.html"
        
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # log_entry = f"[{current_time}] {prompt}\n"
        # print(f"[Log Image]  [{current_time}] {prompt}\n")

        # Write the log entry to the dynamically named file
        with open(log_file_name, "a") as file:
            file.write('<br><br>')
            if title:
                file.write(f"<h2>[{current_time}] {title}</h2>")
            else
                file.write(f"<h2>[{current_time}]</h2>")
            if description:
                file.write(f"<p>{description}</>")
            # Output images in HTML format if found
            if image_strings:
                for img_str in image_strings:
                    file.write(f"<img style='display:block; width:100px;height:100px;' id='base64image' src='data:image/jpeg;base64,{img_str}' />")
            file.write('<br>')
            file.write(prompt_json_to_html_table(prompt))

        return (image_in,)

def prompt_json_to_html_table(json_data):
    # Start the HTML table
    html = '<table border="1" style="border-collapse: collapse; width: 100%;">'
    html += '<tr><th>Node ID</th><th>Class Type</th><th>Inputs</th></tr>'
    
    for node_id, details in json_data.items():
        class_type = details.get('class_type', 'N/A')
        inputs = details.get('inputs', {})
        
        # Format inputs as a string for display
        inputs_str = ', '.join([f"{key}: {value}" for key, value in inputs.items()])

        # Add a row for each node
        html += f'<tr><td>{node_id}</td><td>{class_type}</td><td>{inputs_str}</td></tr>'
    
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