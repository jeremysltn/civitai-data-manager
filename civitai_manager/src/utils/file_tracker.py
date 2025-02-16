from pathlib import Path
import json
from datetime import datetime

class ProcessedFilesManager:
    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
        self.processed_file = self.output_dir / 'processed_files.json'
        self.processed_files = self._load_processed_files()

    def _load_processed_files(self):
        """Load the list of processed files from JSON"""
        if self.processed_file.exists():
            try:
                with open(self.processed_file, 'r') as f:
                    return json.load(f)
            except:
                return {'files': [], 'last_update': None}
        return {'files': [], 'last_update': None}

    def save_processed_files(self):
        """Save the current list of processed files"""
        with open(self.processed_file, 'w') as f:
            self.processed_files['last_update'] = datetime.now().isoformat()
            json.dump(self.processed_files, f, indent=4)

    def is_file_processed(self, file_path):
        """Check if a file has been processed before"""
        return str(file_path) in self.processed_files['files']

    def add_processed_file(self, file_path):
        """Add a file to the processed list"""
        if str(file_path) not in self.processed_files['files']:
            self.processed_files['files'].append(str(file_path))

    def get_new_files(self, directory_path):
        """Get list of new safetensors files that haven't been processed"""
        all_files = list(Path(directory_path).glob('**/*.safetensors'))
        return [f for f in all_files if not self.is_file_processed(f)]
    
    def update_timestamp(self):
        """Update the last_update timestamp without modifying the files list"""
        self.processed_files['last_update'] = datetime.now().isoformat()
        self.save_processed_files()