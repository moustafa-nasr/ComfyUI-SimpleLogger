import json
import datetime
import numpy as np

# Define a class for the custom node
class LogImageNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": { "image_in": ("IMAGE", {}), "log_title": ("STRING", {"default": "image #"}) },
            "hidden": {
                "unique_id": "UNIQUE_ID",
                "prompt": "PROMPT", 
            }
        }

    RETURN_TYPES = ()
    OUTPUT_NODE = True
    CATEGORY = "Logger"
    FUNCTION = "loog"

    def loog(self, image_in, unique_id, prompt,log_title):
        
        # Get the current date to use in the log file name
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        log_file_name = f"logs/log_{current_date}.html"
        
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # log_entry = f"[{current_time}] {prompt}\n"
        # print(f"[{current_time}] {prompt}\n")

        # Write the log entry to the dynamically named file
        with open(log_file_name, "a") as file:
            file.write('<br><br>')
            file.write(f"<h2>[{current_time}] {log_title}</h2>")
            file.write('<br>')
            file.write(prompt_json_to_html_table(prompt))

        return {}

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
