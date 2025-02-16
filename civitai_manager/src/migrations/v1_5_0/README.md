# Migrations v1.5.0

This directory contains migration scripts for handling breaking changes in version 1.5.0.

## migrate_filenames.py

This script handles the migration of filenames to use the new sanitization rules. It renames both directories and files to match the new format while preserving the original model structure.

### Usage

From the project root directory (where main.py is located):

```bash
# First run in dry-run mode to see what changes would be made
python -m src.civitai_manager.migrations.v1_5_0.migrate_filenames "path/to/models/directory" "path/to/output/directory"

# Then run with --execute to actually perform the changes
python -m src.civitai_manager.migrations.v1_5_0.migrate_filenames "path/to/models/directory" "path/to/output/directory" --execute

# Finally, run the main script with the flag --onlyhtml to regenerate all the paths and html files
python main.py --all "path/to/models/directory" --output "path/to/output/directory" --onlyhtml
```

Arguments:
- `input_dir`: Directory containing the original model files (safetensors)
- `output_dir`: Directory containing the processed files (where HTML and JSON files are)
- `--execute`: Optional flag to actually perform the changes. Without this flag, runs in dry-run mode

Note: Make sure you run this from the project root directory (where main.py is located), not from inside the src directory.

### What it does

For each model in the input directory, the script:

1. Gets the sanitized version of the model name
2. Finds the corresponding directory in the output folder
3. Renames the following files to use the sanitized name:
   - model_name.html
   - model_name_civitai_model.json
   - model_name_civitai_model_version.json
   - model_name_hash.json
   - model_name_metadata.json
   - model_name_preview_*.jpeg/jpg/png/mp4
   - model_name_preview_*.json
   - model_name_preview_*.jpeg/jpg/png/mp4.json

4. Updates processed_files.json:
   - Finds processed_files.json in the output directory
   - Updates each file path to use the sanitized filename
   - Preserves the original directory paths
   - Example:
     ```
     From: "C:\Models\loras\[Style] Model v1.0.safetensors"
     To:   "C:\Models\loras\Style_Model_v1.0.safetensors"
     ```

### Examples of changes

Original files:
```
"Model Name SDXL.html"
"/model-name-%20F/model-name-%20F_preview_1.jpeg"
"model-name- F_preview_1.jpeg.json"
```

After migration:
```
"Model_Name_SDXL.html"
"/model-name-_F/model-name-_F_preview_1.jpeg"
"model_name-_F_preview_1.json"
```

The script handles both JSON file patterns:
1. `model_name_preview_N.json` - Standard pattern
2. `model_name_preview_N.ext.json` - Pattern with media extension caused by a previous bug

### Safety Features

1. Dry-run mode by default
   - Shows what changes would be made without actually making them
   - Use --execute flag to actually perform the changes

2. Validation checks
   - Verifies input and output directories exist
   - Checks if files exist before attempting to rename
   - Skips models that don't need changes

3. Error handling
   - Handles errors for individual files without stopping the entire process
   - Reports errors clearly for troubleshooting
