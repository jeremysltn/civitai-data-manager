# Civitai Data Manager

A lightweight tool to locally manage, back up, and organize SafeTensors model metadata from Civitai.

## 🖥️ Demo

![Civitai Data Manager Demo](https://i.imgur.com/FfmROxQ.gif)

## ✨ Features

- **📂 Backup Crucial Info**: Save model metadata, trigger words, usage notes, examples and authors.
- **🖼️ HTML Browser**: Generate interactive HTML pages for browsing your collection.
- **🚀 Smart Updates**: Update only when new data is available.
- **✔️ Broad Compatibility**: Supports `.safetensors` models on Civitai (Checkpoints, LoRA, LyCORIS, etc.).
- **🔒 Lightweight & Free**: No API key required, and highly efficient.

## 🚀 Getting Started

### Requirements
- Python 3.10 or higher

### Installation

1. Clone the repository:
```bash
git clone https://github.com/jeremysltn/civitai-data-manager.git
```

2. Navigate to the project directory:
```bash
cd civitai-data-manager
```

3. Install dependencies:
```bash
# Using Poetry (recommended):
poetry install

# Using pip:
pip install -r requirements.txt
```

4. To verify the installation, try running the script with the help flag:
```bash
python -m civitai_manager.main --help
```

You should see the available command-line options displayed.

## 📖 Usage Guide

You have two ways to use this tool: using a config.json file or options arguments.

### Configuration File (Recommended)

Edit the `config.json` file in the script directory with your preferred settings. If present, the config file takes precedence over command-line arguments.

Example config for first use (save as `config.json`):
```json
{
    "all": "path/to/models/directory",
    "output": "path/to/output/directory",
    "images": true
}
```

Examples of configuration are located in the `config_examples` directory.

### Basic Usage

- The first time, edit the `config.json` file and simply run:
  ```bash
  python -m civitai_manager.main
- To update with the data from newly added models, run periodically to catch updates with the update config (file present in `/config_examples/config.update.json`)

### Command Options
#### Input and Output:
- `--single`: Process a single model file:
  ```bash
  python -m civitai_manager.main --single "path/to/model.safetensors"
  ```
- `--all`: Process all models in a directory:
  ```bash
  python -m civitai_manager.main --all "path/to/model/directory"
  ```
- `--output`: Set an output directory:
  ```bash
  python -m civitai_manager.main --all "path/to/models" --output "path/to/output"
  ```

#### Image Options:
- `--images`: Download all preview images.
- `--noimages`: Skip downloading preview images.
- `--generateimagejson`: Create JSON metadata for preview images.

#### Processing Options:
- `--onlynew`: Process only new files.
- `--skipmissing`: Skip previously missing models.
- `--onlyupdate`: Update metadata for processed models.
- `--clean`: Remove data for models no longer in the source directory.

#### HTML Generation:
- `--onlyhtml`: Generate HTML files from existing data only.

#### Advanced Options:
- `--noconfig`: Ignore `config.json` and use only command-line arguments.
- `--notimeout`: Disable rate limiting protection (use cautiously).


### Recommended Organization

For better organization, run separately for each model category:

```bash
# For checkpoints
python -m civitai_manager.main --all "path/to/checkpoints/sdxl" --output "path/to/backup/checkpoints/sdxl" --noconfig
python -m civitai_manager.main --all "path/to/checkpoints/flux" --output "path/to/backup/checkpoints/flux" --noconfig

# For Loras
python -m civitai_manager.main --all "path/to/loras/sdxl" --output "path/to/backup/loras/sdxl" --noconfig
python -m civitai_manager.main --all "path/to/loras/flux" --output "path/to/backup/loras/flux" --noconfig
```

### Best Practices

- If you want to update only the Civitai data, use the options `--onlyupdate` and `--noimages`
- Just in case, always back up the generated data directory with your models
- Monitor `missing_from_civitai.txt` and `duplicate_models.txt` for manual documentation needs

## 🗃️ Output Structure

### Directory Layout

```
output_directory/
├── model_name/
│   ├── model_name_metadata.json              # SafeTensors metadata
│   ├── model_name_hash.json                  # SHA256 hash
│   ├── model_name_civitai_model_version.json # Model-versions endpoint data from Civitai
│   ├── model_name_civitai_model.json         # Full model data from Civitai
│   ├── model_name_preview_0.jpeg             # First preview image
│   ├── model_name_preview_0.json             # Metadata for first preview image
│   ├── model_name_preview_x.jpeg             # Additional preview images (if --images used)
│   ├── model_name_preview_x.json             # Metadata for additional preview images (if --images used)
│   └── model_name.html                       # Model-specific HTML page
├── index.html                                # Model browser
├── missing_from_civitai.txt                  # List of models not found on Civitai
├── duplicate_models.txt                      # List of duplicate models
└── processed_files.json                      # List of processed files
```

## 🔍 Features in Detail

### Rate Limiting Protection
- Default: random delay between 3-6 seconds after each model and 1 second between each picture
- Disable with `--notimeout` flag (use cautiously)

For example, processing 10 models (with 10 pictures each) would take:
- Minimum time: ~127 seconds
- Maximum time: ~154 seconds
- Average time: ~140.5 seconds

**Note about Rate Limiting:** While Civitai's exact rate limiting policies are not publicly documented, these delays are implemented as a precautionary measure to:
- Be respectful to Civitai's servers
- Avoid getting your requests blocked

If you do not have a lot of files to process, you can disable these delays using the `--notimeout` flag.

### Update Checking
- The script compares Civitai's `updatedAt` timestamp with local data and only processes models with new versions
- Prevents unnecessary API calls and downloads

### Download Images
- The script can download all preview images for your models using the `--images` flag.
- You can disable the images downloading by using the `--noimages` flag.
- By default, only the first preview image will be downloaded.

### HTML Generation
- Individual HTML files for each model showing detailed information and image gallery with generation details
- Global model browser with:
  - Models grouped by type (checkpoint, lora, etc.)
  - Search functionality (tag, filename, model name)
  - By default, models are sorted by Download count
  - Links to individual model and direct download pages

### Processed Files Tracking
- Maintains a JSON file listing all processed models
- Enables selective processing of new files with `--onlynew`
- Records processing timestamp for each file

## ❓ FAQ

### How can you retrieve trigger words for a deleted Lora from Civitai?

If the Lora model has been deleted from Civitai, the script can still generate a `metadata.json` file. Inside this file, look for the JSON properties `"ss_datasets.tag_frequency"` and `"ss_tag_frequency"`, where you'll find the tags associated with the model. It is not certain that these properties are present. In the future, consider using this script regularly to archive all useful information.

### How does this tool compare to other models or Civitai managers?

This tool stands out for its simplicity and lightweight design. It requires no configuration and operates independently of any WebUI (such as A1111, ComfyUI, etc.). With a single command, it scans your models directory, gathers informations on Civitai, and generates an interactive model browser (`index.html`).

## 📘 Additional Information

### Features
[Changelog](CHANGELOG.md) / [Roadmap](ROADMAP.md)

### Contributing
Feel free to open issues or submit pull requests with improvements.

### License
[MIT License](LICENSE.md)

### Acknowledgments
In accordance with Civitai's Terms of Service, this tool adheres to the restriction of not accessing, searching, or utilizing any part of the service through unauthorized engines, software, or tools. It only uses the search agents provided by Civitai through their [official open API](https://github.com/civitai/civitai/wiki/REST-API-Reference), ensuring full compliance with the terms.
