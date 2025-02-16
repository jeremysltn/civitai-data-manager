import os
from pathlib import Path
import json
import sys
import hashlib
import shutil
from datetime import datetime
import time
import random

from civitai_manager import __version__
from ..utils.file_tracker import ProcessedFilesManager
from ..utils.string_utils import sanitize_filename
from ..utils.html_generators.model_page import generate_html_summary

try:
    import requests
except ImportError:
    print("Error: 'requests' module not found. Please install it using:")
    print("pip install requests")
    sys.exit(1)

def get_output_path(clean=False):
    """
    Get output path from user and create necessary directories.
    If no path is provided (empty input), use current directory.
    
    Returns:
        Path: Base output directory path
    """
    while True:
        if clean:
            output_path = input("Enter the path you want to clean (press Enter for current directory): ").strip()
        else:
            output_path = input("Enter the path where you want to save the exported files (press Enter for current directory): ").strip()
        
        # Use current directory if input is empty
        if not output_path:
            path = Path.cwd() / 'output'
            print(f"Using current directory: {path}")
        else:
            path = Path(output_path)
        
        if not path.exists():
            try:
                create = input(f"Directory {path} doesn't exist. Create it? (y/n): ").lower()
                if create == 'y':
                    path.mkdir(parents=True, exist_ok=True)
                else:
                    continue
            except Exception as e:
                print(f"Error creating directory: {str(e)}")
                continue
        
        if not os.access(path, os.W_OK):
            print("Error: No write permission for this directory")
            continue
            
        return path

def setup_export_directories(base_path, safetensors_path):
    """
    Create dated export directory and model-specific subdirectory
    
    Args:
        base_path (Path): Base output directory path
        safetensors_path (Path): Path to the safetensors file
        
    Returns:
        Path: Path to the model-specific directory
    """
    
    # Create dated directory
    # current_date = datetime.now()
    # dated_dir = base_path / f"safetensors-export-{current_date.year}-{current_date.month:02d}-{current_date.day:02d}"
    # dated_dir.mkdir(exist_ok=True)
    
    # Create model-specific directory using sanitized safetensors filename
    sanitized_name = sanitize_filename(safetensors_path.stem)
    model_dir = base_path / sanitized_name
    model_dir.mkdir(exist_ok=True)
    
    return model_dir

def calculate_sha256(file_path, buffer_size=65536):
    """Calculate SHA256 hash of a file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while True:
            data = f.read(buffer_size)
            if not data:
                break
            sha256_hash.update(data)
    return sha256_hash.hexdigest()

def extract_metadata(file_path, output_dir):
    """
    Extract metadata from a .safetensors file
    
    Args:
        file_path (str): Path to the .safetensors file
        output_dir (Path): Directory to save the output
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File {path} not found")
        
        if path.suffix != '.safetensors':
            raise ValueError("File must have .safetensors extension")
        
        base_name = sanitize_filename(path.stem)
        metadata_path = output_dir / f"{base_name}_metadata.json"
        
        # Read just the first line for metadata
        with open(path, 'rb') as f:
            # Read header length (8 bytes, little-endian)
            header_length = int.from_bytes(f.read(8), 'little')
            
            # Read the header
            header_bytes = f.read(header_length)
            header_str = header_bytes.decode('utf-8')
            
            try:
                # Parse the JSON header
                header_data = json.loads(header_str)
                
                # Write metadata to JSON file
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    if "__metadata__" in header_data:
                        json.dump(header_data["__metadata__"], f, indent=4)
                    else:
                        json.dump(header_data, f, indent=4)
                print(f"Metadata successfully extracted to {metadata_path}")
                return True
                
            except json.JSONDecodeError:
                print("Error: Could not parse metadata JSON")
                return False
                
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def extract_hash(file_path, output_dir):
    """
    Calculate hash of a .safetensors file and save it as JSON
    
    Args:
        file_path (str): Path to the .safetensors file
        output_dir (Path): Directory to save the output
    Returns:
        str: Hash value if successful, None otherwise
    """
    try:
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File {path} not found")
        
        hash_value = calculate_sha256(path)
        base_name = sanitize_filename(path.stem)  # Gets sanitized filename without extension
        hash_path = output_dir / f"{base_name}_hash.json"
        
        # Create hash JSON object
        hash_data = {
            "hash_type": "SHA256",
            "hash_value": hash_value,
            "filename": path.name,
            "timestamp": datetime.now().isoformat()
        }
        
        # Write hash to JSON file
        with open(hash_path, 'w', encoding='utf-8') as f:
            json.dump(hash_data, f, indent=4)
        print(f"Hash successfully saved to {hash_path}")
        
        return hash_value
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return None
    
def download_preview_image(image_url, output_dir, base_name, index=None, is_video=False, image_data=None):
    """
    Download a preview image from Civitai
    
    Args:
        image_url (str): URL of the image to download
        output_dir (Path): Directory to save the image
        base_name (str): Base name of the safetensors file
        index (int, optional): Image index for multiple images
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not image_url:
            return False
            
        # Remove the width parameter to get full size image
        url_parts = image_url.split('/')
        if 'width=' in url_parts[-2]:
            url_parts.pop(-2)
        full_size_url = '/'.join(url_parts)
        
        print(f"\nDownloading preview image:")
        print(f"URL: {full_size_url}")
        
        response = requests.get(full_size_url, stream=True)
        if response.status_code == 200:
            # Get the extension from the URL
            # image_name = url_parts[-1]
            ext = '.mp4' if is_video else Path(url_parts[-1]).suffix
            # Add index to sanitized filename if provided
            sanitized_base = sanitize_filename(base_name)
            image_filename = f"{sanitized_base}_preview{f'_{index}' if index is not None else ''}{ext}"
            image_path = output_dir / image_filename
            
            # Download and save the image
            with open(image_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            # Download and save the metadata associated with the image
            if image_data:
                json_filename = f"{Path(image_filename).stem}.json"
                json_path = output_dir / json_filename
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(image_data, f, indent=4)

            print(f"Preview image successfully saved to {image_path}")
            return True
        else:
            print(f"Error: Could not download image (Status code: {response.status_code})")
            return False
            
    except Exception as e:
        print(f"Error downloading preview image: {str(e)}")
        return False

def generate_image_json_files(base_output_path):
    """
    Generate JSON files for all preview images from existing model version data
    
    Args:
        base_output_path (Path): Base output directory path
    """
    print("\nGenerating JSON files for preview images...")
    
    # Find all model version JSON files
    version_files = list(Path(base_output_path).glob('*/*_civitai_model_version.json'))
    total_generated = 0
    
    for version_file in version_files:
        try:
            # Read version data
            with open(version_file, 'r', encoding='utf-8') as f:
                version_data = json.load(f)
            
            # Get model directory
            model_dir = version_file.parent
            
            # Process each image in the version data
            if 'images' in version_data:
                for i, image_data in enumerate(version_data['images']):
                    # Determine the preview file extension
                    ext = '.mp4' if image_data.get('type') == 'video' else '.jpeg'
                    preview_file = model_dir / f"{model_dir.name}_preview_{i}{ext}"
                    
                    # Only create JSON if the preview file exists
                    if preview_file.exists():
                        json_file = preview_file.with_suffix('.json')
                        
                        # Write image metadata
                        with open(json_file, 'w', encoding='utf-8') as f:
                            json.dump(image_data, f, indent=4)
                            total_generated += 1
                            
        except Exception as e:
            print(f"Error processing {version_file}: {str(e)}")
            continue
    
    print(f"\nGenerated {total_generated} JSON files for preview images")
    return True

def update_missing_files_list(base_path, safetensors_path, status_code):
    """
    Update the list of files missing from Civitai
    
    Args:
        base_path (Path): Base output directory path
        safetensors_path (Path): Path to the safetensors file
        status_code (int): HTTP status code from Civitai API
    """
    missing_file = base_path / "missing_from_civitai.txt"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Read existing entries if file exists, skipping header lines
    entries = []
    if missing_file.exists():
        with open(missing_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Extract filename from the entry
                    filename = line.split(' | ')[-1]
                    # Keep entries for other files
                    if filename != safetensors_path.name:
                        entries.append(line)
    
    # Add new entry if file is missing
    if status_code is not None:
        new_entry = f"{timestamp} | Status {status_code} | {safetensors_path.name}"
        entries.append(new_entry)
    
    if entries:
        # Write updated list with headers
        with open(missing_file, 'w', encoding='utf-8') as f:
            f.write("# Files not found on Civitai\n")
            f.write("# Format: Timestamp | Status Code | Filename\n")
            f.write("# This file is automatically updated when the script runs\n")
            f.write("# A file is removed from this list when it becomes available again\n\n")
            
            # Write entries sorted by timestamp (newest first)
            for entry in sorted(entries, reverse=True):
                f.write(f"{entry}\n")
    elif missing_file.exists():
        # Delete the file if there are no entries
        missing_file.unlink()
        print("\nAll models are now available on Civitai. Removed missing_from_civitai.txt")

def find_duplicate_models(directory_path, base_output_path):
    """
    Find models with duplicate hashes
    
    Args:
        directory_path (Path): Directory containing safetensors files
        base_output_path (Path): Base output directory path
        
    Returns:
        dict: Dictionary mapping hashes to lists of model info
    """
    hash_map = {}
    
    # Scan all processed models
    for model_dir in base_output_path.iterdir():
        if not model_dir.is_dir():
            continue
            
        hash_file = model_dir / f"{model_dir.name}_hash.json"
        if not hash_file.exists():
            continue
            
        try:
            with open(hash_file, 'r', encoding='utf-8') as f:
                hash_data = json.load(f)
                hash_value = hash_data.get('hash_value')
                if not hash_value:
                    continue
                    
                # Find corresponding safetensors file
                safetensors_file = None
                for file in Path(directory_path).glob('**/*.safetensors'):
                    if file.stem == model_dir.name:
                        safetensors_file = file
                        break
                
                if not safetensors_file:
                    continue
                    
                if hash_value not in hash_map:
                    hash_map[hash_value] = []
                    
                hash_map[hash_value].append({
                    'model_dir': model_dir,
                    'safetensors_file': safetensors_file,
                    'processed_time': hash_data.get('timestamp')
                })
                
        except Exception as e:
            print(f"Error reading hash file {hash_file}: {e}")
            continue
            
    return {k: v for k, v in hash_map.items() if len(v) > 1}

def clean_output_directory(directory_path, base_output_path):
    """
    Clean up output directory by removing data for models that no longer exist
    
    Args:
        directory_path (Path): Directory containing the safetensors files
        base_output_path (Path): Base output directory path
    """

    print("\nStarting cleanup process (duplicates)...")

    # First handle duplicates
    duplicates = find_duplicate_models(directory_path, base_output_path)
    duplicate_file = None
    
    if duplicates:
        duplicate_file = base_output_path / "duplicate_models.txt"
        with open(duplicate_file, 'w', encoding='utf-8') as f:
            f.write("# Duplicate models found in input directory\n")
            f.write("# Format: Hash | Kept Model | Removed Duplicates\n")
            f.write("# This file is automatically updated when running --clean\n\n")
            
            for hash_value, models in duplicates.items():
                # Sort by processed time, newest first
                sorted_models = sorted(models, 
                    key=lambda x: x['processed_time'] if x['processed_time'] else '',
                    reverse=True
                )
                
                # Keep the newest one, remove others
                kept_model = sorted_models[0]
                removed_models = sorted_models[1:]
                
                # Write to duplicates file
                f.write(f"Hash: {hash_value}\n")
                f.write(f"Kept: {kept_model['safetensors_file']}\n")
                f.write("Removed:\n")
                
                for model in removed_models:
                    f.write(f"  - {model['safetensors_file']}\n")
                    print(f"Removing duplicate model: {model['model_dir'].name}")
                    try:
                        shutil.rmtree(model['model_dir'])
                    except Exception as e:
                        print(f"Error removing directory {model['model_dir']}: {e}")
                f.write("\n")    
 
        print(f"\nDuplicate models list saved to {duplicate_file}")
    else:
        print("\nNo duplicates to remove")

    print("\nStarting cleanup process (removed models)...")
    # Then handle missing models
    # Get list of all current safetensors files (without extension)
    existing_models = {
        Path(file).stem
        for file in Path(directory_path).glob('**/*.safetensors')
    }
    
    # Check each directory in output
    output_dirs = [d for d in base_output_path.iterdir() if d.is_dir()]
    cleaned_dirs = []
    
    for output_dir in output_dirs:
        if output_dir.name not in existing_models:
            print(f"Removing directory: {output_dir.name} (model not found)")
            try:
                shutil.rmtree(output_dir)
                cleaned_dirs.append(str(output_dir))
            except Exception as e:
                print(f"Error removing directory {output_dir}: {e}")
    
    # Update processed_files.json
    if cleaned_dirs:
        files_manager = ProcessedFilesManager(base_output_path)
        new_processed_files = [
            f for f in files_manager.processed_files['files']
            if Path(f).stem in existing_models
        ]
        files_manager.processed_files['files'] = new_processed_files
        files_manager.save_processed_files()
        
        print(f"\nCleaned up {len(cleaned_dirs)} directories")
    else:
        print("\nNo directories to clean")
    
    return True

def fetch_version_data(hash_value, output_dir, base_path, safetensors_path, download_all_images=False, skip_images=False):
    """
    Fetch version data from Civitai API using file hash
    
    Args:
        hash_value (str): SHA256 hash of the file
        output_dir (Path): Directory to save the output
        base_path (Path): Base output directory path
        safetensors_path (Path): Path to the safetensors file
        download_all_images (bool): Whether to download all available preview images
        skip_images (bool): Whether to skip downloading images completely
    Returns:
        int or None: modelId if successful, None otherwise
    """
    try:
        civitai_url = f"https://civitai.com/api/v1/model-versions/by-hash/{hash_value}"
        print(f"\nFetching version data from Civitai API:")
        print(civitai_url)
        
        response = requests.get(civitai_url)
        base_name = sanitize_filename(safetensors_path.stem)
        civitai_path = output_dir / f"{base_name}_civitai_model_version.json"
        
        if response.status_code == 200:
            with open(civitai_path, 'w', encoding='utf-8') as f:
                response_data = response.json()
                json.dump(response_data, f, indent=4)
                print(f"Version data successfully saved to {civitai_path}")

                # Remove from missing files list if it was there before
                update_missing_files_list(base_path, safetensors_path, None)  # Pass None to indicate file is back
                
                # Handle image downloads based on flags
                if not skip_images and 'images' in response_data and response_data['images']:
                    if download_all_images:
                        print(f"\nDownloading all preview images ({len(response_data['images'])} images found)")
                        for i, image_data in enumerate(response_data['images']):
                            if 'url' in image_data:
                                is_video = image_data.get('type') == 'video'
                                download_preview_image(image_data['url'], output_dir, base_name, i, is_video, image_data)
                                # Add a small delay between downloads to be nice to the server
                                if i < len(response_data['images']) - 1:
                                    time.sleep(1)
                    else:
                        # Download only the first image
                        if 'url' in response_data['images'][0]:
                            is_video = response_data['images'][0].get('type') == 'video'
                            download_preview_image(response_data['images'][0]['url'], output_dir, base_name, 0, is_video, response_data['images'][0])

                
                # Return modelId if it exists
                return response_data.get('modelId')
        else:
            error_message = {
                "error": "Failed to fetch Civitai data",
                "status_code": response.status_code,
                "timestamp": datetime.now().isoformat()
            }
            with open(civitai_path, 'w', encoding='utf-8') as f:
                json.dump(error_message, f, indent=4)
            print(f"Error: Failed to fetch Civitai data (Status code: {response.status_code})")
            
            # Update missing files list
            update_missing_files_list(base_path, safetensors_path, response.status_code)
            return None
                
    except Exception as e:
        print(f"Error fetching version data: {str(e)}")
        # Update missing files list for connection errors
        # update_missing_files_list(base_path, safetensors_path, 0)  # Use 0 for connection errors
        return None

def fetch_model_details(model_id, output_dir, safetensors_path):
    """
    Fetch detailed model information from Civitai API
    
    Args:
        model_id (int): The model ID from Civitai
        output_dir (Path): Directory to save the output
        safetensors_path (Path): Path to the safetensors file
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        civitai_model_url = f"https://civitai.com/api/v1/models/{model_id}"
        print(f"\nFetching model details from Civitai API:")
        print(civitai_model_url)
        
        response = requests.get(civitai_model_url)
        base_name = sanitize_filename(safetensors_path.stem)
        model_data_path = output_dir / f"{base_name}_civitai_model.json"
        
        with open(model_data_path, 'w', encoding='utf-8') as f:
            if response.status_code == 200:
                json.dump(response.json(), f, indent=4)
                print(f"Model details successfully saved to {model_data_path}")
                return True
            else:
                error_data = {
                    "error": "Failed to fetch model details",
                    "status_code": response.status_code,
                    "timestamp": datetime.now().isoformat()
                }
                json.dump(error_data, f, indent=4)
                print(f"Error: Could not fetch model details (Status code: {response.status_code})")
                return False
                
    except Exception as e:
        print(f"Error fetching model details: {str(e)}")
        return False

def check_for_updates(safetensors_path, output_dir, hash_value):
    """
    Check if the model needs to be updated by comparing updatedAt timestamps
    
    Args:
        safetensors_path (Path): Path to the safetensors file
        output_dir (Path): Directory where files are saved
        hash_value (str): SHA256 hash of the safetensors file
        
    Returns:
        bool: True if update is needed, False if files are up to date
    """
    try:
        # Check if files exist
        civitai_version_file = output_dir / "civitai_version.txt"
        if not civitai_version_file.exists():
            return True
            
        # Read existing version data
        try:
            with open(civitai_version_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                existing_updated_at = existing_data.get('updatedAt')
                if not existing_updated_at:
                    return True
        except (json.JSONDecodeError, KeyError):
            return True
            
        # Fetch current version data from Civitai
        civitai_url = f"https://civitai.com/api/v1/model-versions/by-hash/{hash_value}"
        print(f"\nChecking for updates from Civitai API:")
        print(civitai_url)
        
        response = requests.get(civitai_url)
        if response.status_code != 200:
            print(f"Error checking for updates (Status code: {response.status_code})")
            return True
            
        current_data = response.json()
        current_updated_at = current_data.get('updatedAt')
        
        if not current_updated_at:
            return True
            
        # Compare timestamps
        if current_updated_at == existing_updated_at:
            print(f"\nModel {safetensors_path.name} is up to date (Last updated: {existing_updated_at})")
            return False
        else:
            print(f"\nUpdate available for {safetensors_path.name}")
            print(f"Current version: {existing_updated_at}")
            print(f"New version: {current_updated_at}")
            return True
            
    except Exception as e:
        print(f"Error checking for updates: {str(e)}")
        return True  # If there's any error, proceed with update

def process_single_file(safetensors_path, base_output_path, download_all_images=False,
                        skip_images=False, html_only=False, only_update=False):
    """
    Process a single safetensors file
    
    Args:
        safetensors_path (Path): Path to the safetensors file
        base_output_path (Path): Base path for output
        download_all_images (bool): Whether to download all available preview images
        skip_images (bool): Whether to skip downloading images completely
        html_only (bool): Whether to only generate HTML files
        only_update (bool): Whether to only update existing processed files
    """

    if not safetensors_path.exists():
        print(f"Error: File {safetensors_path} not found")
        return False
        
    if safetensors_path.suffix != '.safetensors':
        print(f"Error: File {safetensors_path} is not a safetensors file")
        return False
    
    # Setup export directories
    model_output_dir = setup_export_directories(base_output_path, safetensors_path)
    print(f"\nProcessing: {safetensors_path.name}")
    if not html_only:
        print(f"Files will be saved in: {model_output_dir}")
    
    if html_only:
        # Check if required files exist
        base_name = sanitize_filename(safetensors_path.stem)
        required_files = [
            model_output_dir / f"{base_name}_civitai_model.json",
            model_output_dir / f"{base_name}_civitai_model_version.json",
            model_output_dir / f"{base_name}_hash.json"
        ]
        
        if not all(f.exists() for f in required_files):
            print(f"Error: Missing required JSON files for {safetensors_path.name}")
            return False
            
        # Generate HTML only
        generate_html_summary(model_output_dir, safetensors_path)
        return True
    
    if only_update:
        # Check if hash file exists
        hash_file = model_output_dir / f"{safetensors_path.stem}_hash.json"
        if not hash_file.exists():
            print(f"Skipping {safetensors_path.name} (not previously processed)")
            return False
            
        # Read existing hash
        try:
            with open(hash_file, 'r') as f:
                hash_data = json.load(f)
                hash_value = hash_data.get('hash_value')
                if not hash_value:
                    raise ValueError("Invalid hash file")
        except Exception as e:
            print(f"Error reading hash file: {e}")
            return False
    else:
        # Normal processing mode
        hash_value = extract_hash(safetensors_path, model_output_dir)
        if not hash_value:
            print("Error: Failed to extract hash")
            return False
    
    # Check if update is needed
    if not check_for_updates(safetensors_path, model_output_dir, hash_value):
        print("Skipping file (no updates available)")
        return True
    
    # Process the file
    if only_update or extract_metadata(safetensors_path, model_output_dir):
        model_id = fetch_version_data(hash_value, model_output_dir, base_output_path, 
                                    safetensors_path, download_all_images, skip_images)
        if model_id:
            fetch_model_details(model_id, model_output_dir, safetensors_path)
            generate_html_summary(model_output_dir, safetensors_path)
            return True
            
    return False

def process_directory(directory_path, base_output_path, no_timeout=False, 
                     download_all_images=False, skip_images=False, only_new=False, 
                     html_only=False, only_update=False, skip_missing=False):
    """
    Process all safetensors files in a directory
            
    Args:
        directory_path (Path): Path to the directory containing safetensors files
        base_output_path (Path): Base path for output
        no_timeout (bool): If True, disable timeout between files
        download_all_images (bool): Whether to download all available preview images
        skip_images (bool): Whether to skip downloading images completely
        only_new (bool): Whether to only process new models
        html_only (bool): Whether to only generate HTML files
        only_update (bool): Whether to only update existing processed files
    """

    if not directory_path.exists():
        print(f"Error: Directory {directory_path} not found")
        return False
        
    # Initialize processed files manager if needed
    files_manager = None if html_only else ProcessedFilesManager(base_output_path)
    
    # Get files to process
    if only_new and not html_only:
        safetensors_files = files_manager.get_new_files(directory_path)
        if not safetensors_files:
            print("No new files to process")
            return True
        
        if skip_missing:
            # Read missing models file
            missing_file = Path(base_output_path) / 'missing_from_civitai.txt'
            missing_models = set()
            if missing_file.exists():
                with open(missing_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip() and not line.startswith('#'):
                            filename = line.strip().split(' | ')[-1]
                            missing_models.add(filename)
                            
            # Filter out previously missing models
            safetensors_files = [
                f for f in safetensors_files 
                if f.name not in missing_models
            ]
            if not safetensors_files:
                print("No new non-missing files to process")
                return True

        print(f"\nFound {len(safetensors_files)} new .safetensors files")
    elif only_update:
        # Only get previously processed files
        safetensors_files = []
        all_files = list(directory_path.glob('**/*.safetensors'))
        for file_path in all_files:
            hash_file = Path(base_output_path) / file_path.stem / f"{file_path.stem}_hash.json"
            if hash_file.exists():
                safetensors_files.append(file_path)
        print(f"\nFound {len(safetensors_files)} previously processed files")
    else:
        safetensors_files = list(directory_path.glob('**/*.safetensors'))
        if not safetensors_files:
            print(f"No .safetensors files found in {directory_path}")
            return False
        print(f"\nFound {len(safetensors_files)} .safetensors files")
    
    if html_only:
        print("HTML only mode: Skipping data fetching")
    
    files_processed = 0
    for i, file_path in enumerate(safetensors_files, 1):
        print(f"\n[{i}/{len(safetensors_files)}] Processing: {file_path.relative_to(directory_path)}")
        success = process_single_file(file_path, base_output_path, 
                                    download_all_images, skip_images, html_only, only_update)
        
        if success:
            files_processed += 1
            if not html_only:
                if not only_update:
                    files_manager.add_processed_file(file_path)
                else:
                    files_manager.update_timestamp()            
        
        # Add timeout between files (except for the last file) if not in HTML only mode
        if not html_only and not no_timeout and i < len(safetensors_files):
            timeout = random.uniform(3, 6)
            print(f"\nWaiting {timeout:.1f} seconds before processing next file (rate limiting protection)...")
            print("(You can use --notimeout to disable this waiting time)")
            time.sleep(timeout)
    
    # Save the updated processed files list if not in HTML only mode
    if not (html_only or only_update):
        files_manager.save_processed_files()

    return True
