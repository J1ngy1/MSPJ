from flask import Flask, render_template, request, redirect, url_for, jsonify
from openai import OpenAI
import os
import yaml
import glob
import difflib
from datetime import datetime



app = Flask(__name__)

OPENAI_API_KEY  = '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'

DOCKER_COMPOSE_PATH = os.getenv('DOCKER_COMPOSE_PATH', '/app/')



def save_config_history(config):
    history_dir = os.path.join(os.path.dirname(DOCKER_COMPOSE_PATH), 'history')
    os.makedirs(history_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    history_file_path = os.path.join(history_dir, f'docker-compose_{timestamp}.yml')
    
    with open(history_file_path, 'w') as f:
        f.write(config)

@app.route('/')
def home():
    try:
        # 定义 YAML 搜索目录
        directory = os.getenv('DOCKER_COMPOSE_PATH', '/app/')
        history_dir = os.path.join(directory, 'history')

        print(f"✅ [DEBUG] DOCKER_COMPOSE_PATH: {directory}")  # 确保路径正确
        print(f"✅ [DEBUG] Looking for YAML files in {directory}...")

        # 查找所有 YAML 文件（递归搜索）
        yaml_files = glob.glob(os.path.join(directory, '**/*.yml'), recursive=True)
        yaml_files += glob.glob(os.path.join(directory, '**/*.yaml'), recursive=True)

        print(f"✅ [DEBUG] Found YAML files: {yaml_files}")  # 确保找到了 YAML

        # 过滤掉 history 目录中的 YAML 文件
        yaml_files = [file for file in yaml_files if history_dir not in file]

        # 生成 YAML 文件信息
        yaml_files_info = [
            (os.path.relpath(file, directory), os.path.relpath(file, directory)) for file in yaml_files
        ]

        print(f"✅ [DEBUG] Final YAML list: {yaml_files_info}")

        return render_template('home.html', yaml_files_info=yaml_files_info)
    except Exception as e:
        print(f"❌ [ERROR] Error listing YAML files: {str(e)}")
        return f"Error listing YAML files: {str(e)}"

  
@app.route('/generate-config-from-view/<path:file_path>', methods=['POST'])
def generate_config_from_view(file_path):
    try:
        # Define the directory to search for YAML files
        directory = os.path.dirname(DOCKER_COMPOSE_PATH)
        full_path = os.path.join(directory, file_path)

        # Load the content of the selected YAML file (current config)
        with open(full_path, 'r') as f:
            current_config = f.read()

        # Get the user input (description) from the form
        user_input = request.form['description']

        # Generate the new configuration based on the user input
        generated_config = get_chatgpt_generated_config(user_input, current_config)

        # Highlight the differences between the current and new config
        highlighted_current_config, highlighted_new_config = highlight_diff(current_config, generated_config)

        # Render the confirm update page to compare the two configs
        return render_template(
            'confirm_update.html',
            current_config=highlighted_current_config,  # Highlighted current config
            highlighted_new_config=highlighted_new_config,  # Highlighted new config
            new_config=generated_config,  # Plain new config for editing
            version_name="",
              file_name=file_path  # Empty version name field to be filled in
        )
    except Exception as e:
        return f"Error generating configuration: {str(e)}"

@app.route('/view-yaml/<path:file_path>', methods=['GET', 'POST'])
def view_yaml(file_path):
    try:
        directory = os.getenv('DOCKER_COMPOSE_PATH', '/app/')

        # Construct the correct full path
        full_path = os.path.join(directory, file_path.lstrip("/"))  # Strip leading '/' to avoid absolute paths

        print(f"✅ [DEBUG] Full path for YAML file: {full_path}")  # Debugging

        # Check if the file exists before trying to open it
        if not os.path.exists(full_path):
            print(f"❌ [ERROR] File not found: {full_path}")
            return f"Error: File '{file_path}' not found."

        # Read the content of the selected YAML file
        with open(full_path, 'r') as f:
            yaml_content = f.read()

        if request.method == 'POST':
            # Get user input from the form (description)
            user_input = request.form['description']
            
            # Use ChatGPT to generate the new configuration based on user input and the current YAML content
            generated_config = get_chatgpt_generated_config(user_input, yaml_content)

            # Highlight the differences between the current and new configuration
            highlighted_current_config, highlighted_new_config = highlight_diff(yaml_content, generated_config)

            # Render the same page with the highlighted changes
            return render_template(
                'view_yaml.html',
                file_name=file_path,
                yaml_content=yaml_content,
                generated_config=generated_config,  # New generated config
                highlighted_current_config=highlighted_current_config,  # Highlighted current config
                highlighted_new_config=highlighted_new_config  # Highlighted new config
            )

        # Initial GET request to display the page
        return render_template('view_yaml.html', file_name=file_path, yaml_content=yaml_content)

    except Exception as e:
        return f"Error reading YAML file: {str(e)}"

@app.route('/list-yaml-files')
def list_yaml_files():
    try:
        # Define the directory to search
        directory = os.path.dirname(DOCKER_COMPOSE_PATH)
        
        # Use glob to search recursively for all .yml and .yaml files
        yaml_files = glob.glob(os.path.join(directory, '**/*.yml'), recursive=True)
        yaml_files += glob.glob(os.path.join(directory, '**/*.yaml'), recursive=True)

        return render_template('list_yaml_files.html', yaml_files=yaml_files)  # Pass file paths to the template

    except Exception as e:
        return f"Error listing YAML files: {str(e)}"




@app.route('/view-config')
def view_config():
    try:
        # Define the directory to search (DOCKER_COMPOSE_PATH is the parent folder)
        directory = os.path.dirname(DOCKER_COMPOSE_PATH)
        
        # Use glob to search recursively for all .yml and .yaml files
        yaml_files = glob.glob(os.path.join(directory, '**/*.yml'), recursive=True)
        yaml_files += glob.glob(os.path.join(directory, '**/*.yaml'), recursive=True)

        # Prepare a dictionary to hold file paths and contents
        yaml_data = {}
        
        for file in yaml_files:
            with open(file, 'r') as f:
                yaml_data[file] = f.read()  # Store the file path and content
        
        return render_template('view_config.html', yaml_data=yaml_data)  # Pass all YAML files to the template

    except Exception as e:
        return f"Error reading YAML files: {str(e)}"
    
def load_current_config(file_path=None):
    try:
        # If no specific file path is provided, use the default docker-compose path
        if file_path is None:
            file_path = DOCKER_COMPOSE_PATH

        # Check if the path is a file (not a directory)
        if os.path.isdir(file_path):
            return f"Error: {file_path} is a directory, not a file."

        # Open the file and read its content
        with open(file_path, 'r') as file:
            current_config = file.read()  # Load the current configuration as text
            return current_config
    except Exception as e:
        print(f"Error reading YAML file: {str(e)}")  # Debugging for errors
        return f"Error reading YAML file: {str(e)}"

def highlight_diff(current_config, generated_config):
    current_lines = current_config.splitlines()
    new_lines = generated_config.splitlines()

    diff = difflib.ndiff(current_lines, new_lines)

    highlighted_current = []
    highlighted_new = []

    for line in diff:
        if line.startswith('- '):  # Line deleted in the new config
            highlighted_current.append(f'<span class="highlight-del">{line[2:]}</span>')
        elif line.startswith('+ '):  # Line added in the new config
            highlighted_new.append(f'<span class="highlight-add">{line[2:]}</span>')
        elif line.startswith('  '):  # Unchanged line
            highlighted_current.append(line[2:])
            highlighted_new.append(line[2:])
        else:
            pass

    return '\n'.join(highlighted_current), '\n'.join(highlighted_new)

@app.route('/generate-config', methods=['GET', 'POST'])
def generate_config():
    if request.method == 'POST':
        user_input = request.form['user_input']

        # Load the current configuration from a specific file (if needed)
        current_config = load_current_config()

        # Generate the new config using ChatGPT
        generated_config = get_chatgpt_generated_config(user_input, current_config)

        # Highlight differences between current and new config
        highlighted_current_config, highlighted_new_config = highlight_diff(current_config, generated_config)

        return render_template(
            'confirm_update.html',
            current_config=highlighted_current_config,
            highlighted_new_config=highlighted_new_config,
            new_config=generated_config  # Plain version for editing
        )
    
    return render_template('generate_config.html')



@app.route('/confirm-update', methods=['POST'])
def confirm_update():
    edited_new_config = request.form.get('new_config')
    version_name = request.form.get('version_name')  # Get the version name
    file_name = request.form.get('file_name')  # Get the file name (e.g., docker-compose, prometheus)

    if edited_new_config is None:
        return "Error: 'new_config' is missing"

    if not file_name:
        return "Error: 'file_name' is missing"

    # If version_name is missing, pass None so the function will generate a timestamp
    if not version_name:
        version_name = None

    # Save the configuration version in the file's dedicated history folder
    file_path = os.path.join(DOCKER_COMPOSE_PATH, file_name)
    try:
        with open(file_path, 'r') as file:
            old_config = file.read()
    except FileNotFoundError:
        return f"Error: Could not load the current configuration of {file_name}. File not found."
    except Exception as e:
        return f"Error: Failed to read {file_name}: {str(e)}"

    if old_config is None:
        return "Error: Could not load the current configuration."

    # Save the old configuration before overwriting
    save_config_version(old_config, version_name, file_name)

    if request.form.get('confirm') == 'Yes':
        try:
            update_config_file(file_name,edited_new_config)
            restart_docker_compose()
            return render_template('result.html', result=f"Configuration updated successfully!",config=edited_new_config)
        except Exception as e:
            return render_template('result.html', result=f"Error: {str(e)}", config=edited_new_config)

    return redirect(url_for('generate_config'))


def save_config_version(config, version_name, file_name):
    # Get the directory where the main configuration file is located
    base_directory = os.path.dirname(DOCKER_COMPOSE_PATH)

        # Extract directory and filename separately
    file_dir = os.path.dirname(file_name)  # e.g., envoy-dynamic/envoy-server
    base_file_name = os.path.basename(file_name)  # e.g., envoy.yaml

    # Define the correct history directory
    history_dir = os.path.join(base_directory, 'history', file_dir, base_file_name)

    # Ensure the history directory exists
    os.makedirs(history_dir, exist_ok=True)


    # If version_name is None, generate a name based on the current date and time
    if not version_name:
        version_name = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

    # Save the version inside the respective history directory
    version_path = os.path.join(history_dir, f'{version_name}.yml')
    
    try:
        # Write the config to the new version file
        with open(version_path, 'w') as version_file:
            version_file.write(config)
        print(f"Configuration saved as version: {version_name} in {file_name}'s history.")
    except Exception as e:
        print(f"Failed to save version {version_name}: {str(e)}")

@app.route('/view-history/<path:file_path>')
def view_history(file_path):
    print(f"view_history function called with file_path: {file_path}")  # Debugging output
    try:
        # Define the base directory and history path
        directory = os.path.dirname(DOCKER_COMPOSE_PATH)
        history_dir = os.path.join(directory, 'history', file_path)

        print(f"Checking history directory at: {history_dir}")  # Debugging output

        # Check if history_dir is a valid directory
        if os.path.exists(history_dir) and os.path.isdir(history_dir):
            # List only YAML files inside the history directory (skip subdirectories)
            history_files = [
                os.path.join(history_dir, f) 
                for f in os.listdir(history_dir) 
                if os.path.isfile(os.path.join(history_dir, f)) and (f.endswith('.yml') or f.endswith('.yaml'))
            ]
            history_files = sorted(history_files, reverse=True)

            # If no version files are found
            if not history_files:
                print("No history files found.")  # Debugging output
                return render_template('view_history.html', file_name=file_path, history_files=[], message="No history available for this file.")
        else:
            print("History directory not found.")  # Debugging output
            return render_template('view_history.html', file_name=file_path, history_files=[], message="History directory not found for this configuration file.")

        # Passing the history files (just filenames, not full paths)
        history_file_names = [os.path.basename(f) for f in history_files]
        print("History files found:", history_file_names)  # Debugging output
        return render_template('view_history.html', file_name=file_path, history_files=history_file_names, message=None)

    except Exception as e:
        print(f"Error retrieving history for {file_path}: {str(e)}")  # Debugging output
        return f"Error retrieving history for {file_path}: {str(e)}"




@app.route('/revert-history/<filename>')
def revert_history(filename):
    history_dir = os.path.join(os.path.dirname(DOCKER_COMPOSE_PATH), 'history')
    file_path = os.path.join(history_dir, filename)

    try:
        with open(file_path, 'r') as f:
            history_config = f.read()

        update_config_file(history_config)

        return render_template('result.html', result=f"Reverted to {filename} successfully!", config=history_config)
    except Exception as e:
        return f"Error reverting to {filename}: {str(e)}"

@app.route('/view-history-file/<path:file_path>/<version>')
def view_history_file(file_path, version):
    try:
        # Ensure correct base directory
        base_history_dir = os.path.join(os.path.dirname(DOCKER_COMPOSE_PATH), 'history')

        # Construct correct history file path
        history_file_path = os.path.join(base_history_dir, file_path, version)

        print(f"Debug: Corrected file path = {history_file_path}")  # Debugging output

        # Ensure history_file_path is actually a file
        if not os.path.isfile(history_file_path):
            return f"Error: {history_file_path} is not a valid file."

        # Read the history file content
        with open(history_file_path, 'r') as history_file_obj:
            history_content = history_file_obj.read()

        # Construct the source file path (current YAML file)
        source_file_path = os.path.join(DOCKER_COMPOSE_PATH, file_path)
        if not os.path.isfile(source_file_path):
            return f"Error: {source_file_path} is not a valid file."

        with open(source_file_path, 'r') as source_file:
            source_content = source_file.read()

        # Highlight differences
        highlighted_current_config, highlighted_new_config = highlight_diff(source_content, history_content)

        return render_template(
            'view_history_file.html',
            file_name=file_path,
            source_content=highlighted_current_config,
            history_file_name=version,
            history_content=highlighted_new_config
        )

    except Exception as e:
        return f"Error reading history file: {str(e)}"



@app.route('/restore-version/<path:file_path>/<version>', methods=['POST'])
def restore_version(file_path, version):
    try:
        # Base directory
        base_directory = os.path.dirname(DOCKER_COMPOSE_PATH)

        # Path to the version file in the history folder
        version_file_path = os.path.join(base_directory, 'history', file_path, version)

        # Path to the original file (file_path)
        source_file_path = os.path.join(base_directory, file_path)

        # Ensure the version file exists in the history directory
        if not os.path.exists(version_file_path):
            return render_template('result.html', result=f"Error: Version file {version} not found for {file_path}", config="")

        # Copy the version content to overwrite the source file
        with open(version_file_path, 'r') as version_file:
            version_content = version_file.read()

        # Overwrite the original file with the version content
        with open(source_file_path, 'w') as source_file:
            source_file.write(version_content)

        # Use the existing `result.html` template and include a Home button
        return render_template('result.html', result=f"Successfully restored {file_path} using version: {version}", config=version_content)

    except Exception as e:
        return render_template('result.html', result=f"Error restoring version {version} for {file_path}: {str(e)}", config="")



def get_chatgpt_generated_config(prompt, current_config=""):
    system_message = "You are an assistant that helps generate and modify Docker Compose configuration files.The current configuration is provided, and you should only modify the necessary sections based on the user's request. Return the full updated configuration in text YAML format with only the necessary changes. No code block as I want the answer in plaintext that can be used by just copying all."
    full_prompt = f"Current configuration:\n{current_config}\n\nUser request: {prompt}"

    response = OpenAI(api_key=OPENAI_API_KEY).chat.completions.create(
        model="gpt-4o-mini", 
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": full_prompt}
        ]
    )
    response_dict = response.model_dump() 
    print(response_dict["choices"][0]["message"]["content"] )
    return response_dict["choices"][0]["message"]["content"] 

def update_config_file(file_path, updated_config):
    try:
        # Construct the full path to the file
        full_path = os.path.join('/Users/shu/Downloads/IMO-Sidecar-Networking-main', file_path)

        # Check if the path is a directory, and throw an error if it is
        if os.path.isdir(full_path):
            return f"Error: '{full_path}' is a directory, not a file", 400
        
        # Write the updated configuration to the file
        with open(full_path, 'w') as f:
            f.write(updated_config)
        
        print(f"Configuration successfully updated for: {file_path}")
        return None  # No error

    except Exception as e:
        print(f"Failed to update the configuration: {str(e)}")
        return f"Error writing to the file: {str(e)}"


def restart_docker_compose():
    os.system('docker-compose down')
    os.system('docker-compose up -d')
import subprocess

def check_docker_status():
    try:
        result = subprocess.run(['docker', 'ps'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode == 0:
            running_containers = result.stdout.strip()
            if not running_containers:
                return "No containers are currently running."
            return running_containers
        else:
            return f"Error: {result.stderr.strip()}"
    except Exception as e:
        return f"Exception: {str(e)}"


@app.route('/docker-status')
def docker_status():
    status = check_docker_status()  # Get the Docker status
    return render_template('docker_status.html', status=status)


if __name__ == '__main__':
    app.run(debug=True)
