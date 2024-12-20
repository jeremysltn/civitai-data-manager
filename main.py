#!/usr/bin/env python3

import os
import sys
import argparse
from pathlib import Path
from src.civitai_manager.core.metadata_manager import (
    VERSION,
    process_single_file,
    process_directory,
    clean_output_directory,
    generate_image_json_files,
    get_output_path
)
from src.civitai_manager.utils.html_generators.browser_page import generate_global_summary
from src.civitai_manager.utils.config import load_config, ConfigValidationError

def parse_cli_args():
    """Parse and validate command line arguments."""
    parser = argparse.ArgumentParser(description='Process SafeTensors files and fetch Civitai data')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--single', type=str, help='Path to a single .safetensors file')
    group.add_argument('--all', type=str, help='Path to directory containing .safetensors files')
    parser.add_argument('--notimeout', action='store_true', 
                       help='Disable timeout between files (warning: may trigger rate limiting)')
    parser.add_argument('--output', type=str, 
                       help='Output directory path (if not specified, will prompt for it)')
    parser.add_argument('--images', action='store_true',
                       help='Download all available preview images instead of just the first one')
    parser.add_argument('--generateimagejson', action='store_true',
                       help='Generate JSON files for all preview images from existing model version data')
    parser.add_argument('--noimages', action='store_true',
                       help='Skip downloading any preview images')
    parser.add_argument('--onlynew', action='store_true',
                       help='Only process new files that haven\'t been processed before')
    parser.add_argument('--skipmissing', action='store_true',
                       help='Skip previously missing models when used with --onlynew')
    parser.add_argument('--onlyhtml', action='store_true',
                       help='Only generate HTML files from existing JSON data')
    parser.add_argument('--onlyupdate', action='store_true',
                       help='Only update previously processed files, skipping hash calculation')
    parser.add_argument('--clean', action='store_true',
                       help='Remove data for models that no longer exist in the target directory')
    parser.add_argument('--noconfig', action='store_true',
                       help='Ignore config.json and use command line arguments only')


    args = parser.parse_args()
    
    # Validate arguments
    if args.images and args.noimages:
        print("Error: Cannot use both --images and --noimages at the same time")
        sys.exit(1)
    if args.onlynew and args.onlyhtml:
        print("Error: Cannot use both --onlynew and --onlyhtml at the same time")
        sys.exit(1)
    if args.onlyupdate and args.onlynew:
        print("Error: Cannot use both --onlyupdate and --onlynew at the same time")
        sys.exit(1)
    if args.onlyupdate and args.onlyhtml:
        print("Error: Cannot use both --onlyupdate and --onlyhtml at the same time")
        sys.exit(1)
    if args.clean and args.single:
        print("Error: --clean option can only be used with --all")
        sys.exit(1)
    if args.clean and (args.onlyhtml or args.onlyupdate or args.onlynew):
        print("Error: --clean cannot be used with --onlyhtml, --onlyupdate, or --onlynew")
        sys.exit(1)
    
    return args

def get_config():
    """
    Try to load config from file first, fall back to CLI args if no config found
    or if config is invalid. Respect --noconfig flag.
    """
    # Parse CLI args first to check for --noconfig
    args = parse_cli_args()
    
    # If --noconfig is used, only use CLI args
    if args.noconfig:
        print("Using command line arguments (--noconfig specified)")
        config = vars(args)
        config.pop('noconfig')  # Remove noconfig from the config dict
        return config
    
    try:
        config = load_config()
        if config:
            print("Using configuration from config.json")
            return config
    except ConfigValidationError as e:
        print(f"Error in config file: {str(e)}")
        print("Falling back to command line arguments...")
    except Exception as e:
        print(f"Error loading config file: {str(e)}")
        print("Falling back to command line arguments...")
    
    # Convert CLI args to config dict
    config = vars(args)
    config.pop('noconfig')  # Remove noconfig from the config dict
    return config

def main():
    config = get_config()
    
    # Get base output path either from config/argument or user input
    if config.get('output'):
        base_output_path = Path(config['output'])
        if not base_output_path.exists():
            try:
                base_output_path.mkdir(parents=True, exist_ok=True)
                print(f"Created output directory: {base_output_path}")
            except Exception as e:
                print(f"Error creating output directory: {str(e)}")
                sys.exit(1)
        if not os.access(base_output_path, os.W_OK):
            print(f"Error: No write permission for directory {base_output_path}")
            sys.exit(1)
    else:
        base_output_path = get_output_path(clean=config.get('clean', False))
    
    if config.get('single'):
        safetensors_path = Path(config['single'])
        process_single_file(safetensors_path, base_output_path, 
                          download_all_images=config.get('images', False),
                          skip_images=config.get('noimages', False),
                          html_only=config.get('onlyhtml', False),
                          only_update=config.get('onlyupdate', False))
    elif config.get('all'):
        directory_path = Path(config['all'])
        
        if config.get('clean', False):
            clean_output_directory(directory_path, base_output_path)
        elif config.get('generateimagejson', False):
            generate_image_json_files(base_output_path)
        else:
            process_directory(directory_path, base_output_path, 
                            config.get('notimeout', False),
                            download_all_images=config.get('images', False),
                            skip_images=config.get('noimages', False),
                            only_new=config.get('onlynew', False),
                            html_only=config.get('onlyhtml', False),
                            only_update=config.get('onlyupdate', False),
                            skip_missing=config.get('skipmissing', False))
        
    if ('single' in config or 'all' in config):
        generate_global_summary(base_output_path, VERSION)

if __name__ == "__main__":
    main()
