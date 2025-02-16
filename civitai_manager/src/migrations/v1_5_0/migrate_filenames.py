from pathlib import Path
import argparse
import json
from src.civitai_manager.utils.string_utils import sanitize_filename

def update_processed_files(output_dir: Path, dry_run: bool = True):
    """
    Update processed_files.json with sanitized filenames
    
    Args:
        output_dir (Path): Directory containing processed_files.json
        dry_run (bool): If True, only print what would be done without making changes
    """
    processed_files_path = output_dir / "processed_files.json"
    if not processed_files_path.exists():
        print("\nNo processed_files.json found - skipping")
        return
        
    print("\nUpdating processed_files.json...")
    
    try:
        with open(processed_files_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        updated_files = []
        for file_path in data.get('files', []):
            # Split path into directory and filename
            path = Path(file_path)
            dir_path = path.parent
            
            # Sanitize just the filename portion
            sanitized_name = sanitize_filename(path.stem) + path.suffix
            new_path = str(dir_path / sanitized_name)
            
            if new_path != file_path:
                if dry_run:
                    print(f"Would update path:\nFrom: {file_path}\nTo:   {new_path}\n")
                else:
                    print(f"Updating path:\nFrom: {file_path}\nTo:   {new_path}\n")
            
            updated_files.append(new_path)
            
        if not dry_run:
            data['files'] = updated_files
            with open(processed_files_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            print("Updated processed_files.json")
        
    except Exception as e:
        print(f"Error updating processed_files.json: {e}")

def migrate_model_files(input_dir: Path, output_dir: Path, dry_run: bool = True):
    """
    Migrate model files to use sanitized filenames
    
    Args:
        input_dir (Path): Directory containing the model files
        output_dir (Path): Directory containing the output files
        dry_run (bool): If True, only print what would be done without making changes
    """
    print(f"\nScanning input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    if dry_run:
        print("\nDRY RUN MODE - No files will be modified")
    
    # Get all safetensors files
    safetensors_files = list(input_dir.glob('**/*.safetensors'))
    
    for safetensors_file in safetensors_files:
        base_name = safetensors_file.stem
        sanitized_name = sanitize_filename(base_name)
        
        # Check if output directory exists
        model_dir = output_dir / base_name
        if not model_dir.exists():
            print(f"\nSkipping {base_name} - No output directory found")
            continue
            
        print(f"\nProcessing: {base_name}")
        print(f"Sanitized name: {sanitized_name}")
        
        if base_name == sanitized_name:
            print("No changes needed - name already sanitized")
            continue
            
        # Get all files in the model directory
        files_to_rename = []
        
        # Core files
        core_files = [
            f"{base_name}.html",
            f"{base_name}_civitai_model.json",
            f"{base_name}_civitai_model_version.json",
            f"{base_name}_hash.json",
            f"{base_name}_metadata.json"
        ]
        
        # Find preview files by checking what exists
        preview_index = 0
        while True:
            preview_file = model_dir / f"{base_name}_preview_{preview_index}.jpeg"
            json_file = model_dir / f"{base_name}_preview_{preview_index}.json"
            
            if not preview_file.exists():
                # Try other extensions
                found = False
                for ext in ['.jpg', '.png', '.mp4']:
                    alt_file = model_dir / f"{base_name}_preview_{preview_index}{ext}"
                    if alt_file.exists():
                        preview_file = alt_file
                        found = True
                        break
                if not found:
                    break
            
            files_to_rename.append((
                preview_file.name,
                f"{sanitized_name}_preview_{preview_index}{preview_file.suffix}"
            ))
            
            # Check for both JSON file patterns
            json_file_patterns = [
                f"{base_name}_preview_{preview_index}.json", # Standard pattern
                f"{base_name}_preview_{preview_index}{preview_file.suffix}.json" # With extension pattern (a previous bug added image extension to the json filename)
            ]
            
            for json_pattern in json_file_patterns:
                json_file = model_dir / json_pattern
                if json_file.exists():
                    new_json_name = (f"{sanitized_name}_preview_{preview_index}{preview_file.suffix}.json" 
                                   if '.json' in json_pattern 
                                   else f"{sanitized_name}_preview_{preview_index}.json")
                    files_to_rename.append((json_file.name, new_json_name))
            
            preview_index += 1
        
        # Add core files that exist
        for file in core_files:
            file_path = model_dir / file
            if file_path.exists():
                new_name = file.replace(base_name, sanitized_name)
                files_to_rename.append((file, new_name))
        
        # Rename directory first
        new_dir = output_dir / sanitized_name
        if not dry_run:
            try:
                model_dir.rename(new_dir)
                print(f"Renamed directory: {model_dir.name} -> {new_dir.name}")
            except Exception as e:
                print(f"Error renaming directory: {e}")
                continue
        else:
            print(f"Would rename directory: {model_dir.name} -> {new_dir.name}")
        
        # Then rename all files
        for old_name, new_name in files_to_rename:
            old_path = model_dir if dry_run else new_dir
            old_path = old_path / old_name
            new_path = new_dir / new_name
            
            if not dry_run:
                try:
                    old_path.rename(new_path)
                    print(f"Renamed file: {old_name} -> {new_name}")
                except Exception as e:
                    print(f"Error renaming {old_name}: {e}")
            else:
                print(f"Would rename file: {old_name} -> {new_name}")

def main():
    parser = argparse.ArgumentParser(description='Migrate model files to use sanitized filenames')
    parser.add_argument('input_dir', help='Directory containing the model files')
    parser.add_argument('output_dir', help='Directory containing the output files')
    parser.add_argument('--execute', action='store_true', help='Execute the migration (without this flag, runs in dry-run mode)')
    
    args = parser.parse_args()
    
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    
    if not input_dir.exists():
        print(f"Error: Input directory {input_dir} does not exist")
        return
        
    if not output_dir.exists():
        print(f"Error: Output directory {output_dir} does not exist")
        return
    
    migrate_model_files(input_dir, output_dir, dry_run=not args.execute)
    update_processed_files(output_dir, dry_run=not args.execute)

if __name__ == '__main__':
    main()
