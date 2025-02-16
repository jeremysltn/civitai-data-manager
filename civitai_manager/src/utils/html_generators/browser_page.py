from pathlib import Path
import html
from ..string_utils import sanitize_filename
import json
from datetime import datetime
from civitai_manager import __version__

def generate_global_summary(output_dir):
    """
    Generate an HTML summary of all models in the output directory
    
    Args:
        output_dir (Path): Directory containing the JSON files
    """
    try:
        # Find all model.json files
        model_files = list(Path(output_dir).glob('*/*/civitai_model.json')) + \
                      list(Path(output_dir).glob('*/*_civitai_model.json'))
        
        # Read missing models file
        missing_models = set()
        missing_file = Path(output_dir) / 'missing_from_civitai.txt'
        if missing_file.exists():
            with open(missing_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        # Extract filename from the line
                        filename = line.strip().split(' | ')[-1]
                        missing_models.add(filename)
        
        # Dictionary to store models by type
        models_by_type = {}
        
        for model_file in model_files:
            try:
                # Get paths for model, version, and hash files
                base_name = model_file.parent.name
                version_file = model_file.parent / f"{base_name}_civitai_model_version.json"
                hash_file = model_file.parent / f"{base_name}_hash.json"
                html_file = model_file.parent / f"{base_name}.html"
        
                # Read all files
                with open(model_file, 'r', encoding='utf-8') as f:
                    model_data = json.load(f)

                version_data = {}
                if version_file.exists():
                    with open(version_file, 'r', encoding='utf-8') as f:
                        version_data = json.load(f)
                        
                hash_data = {}
                if hash_file.exists():
                    with open(hash_file, 'r', encoding='utf-8') as f:
                        hash_data = json.load(f)

                model_type = model_data.get('type', 'Unknown')
                
                if model_type not in models_by_type:
                    models_by_type[model_type] = []
                    
                models_by_type[model_type].append({
                    # Add model data
                    'name': model_data.get('name') or 'Unknown',
                    'creator': model_data.get('creator', {}).get('username', 'Unknown'),
                    'base_name': base_name,
                    'html_file': f"{base_name}.html",
                    'tags': model_data.get('tags', []),
                    # Add version data
                    'version_name': version_data.get('name', ''),
                    'downloads': version_data.get('stats', {}).get('downloadCount', 0),
                    'has_html': html_file.exists(),
                    'added_date': hash_data.get('timestamp', ''),
                    'file_size': version_data.get('files', [{}])[0].get('sizeKB', None)
                })
            except:
                continue

        # Process missing models
        if missing_models:
            if 'Missing from Civitai' not in models_by_type:
                models_by_type['Missing from Civitai'] = []
            
            for filename in missing_models:
                base_name = Path(filename).stem
                html_file = Path(output_dir) / base_name / f"{base_name}.html"
                html_exists = html_file.exists()

                models_by_type['Missing from Civitai'].append({
                    'name': base_name,
                    'creator': 'Unknown',
                    'downloads': 0,
                    'base_name': base_name,
                    'html_file': f"{base_name}.html" if html_exists else '',
                    'tags': [],
                    'baseModel': 'Unknown',
                    'trainedWords': [],
                    'createdAt': 'Unknown',
                    'updatedAt': 'Unknown',
                    'missing': True,
                    'has_html': html_exists
                })

        # Sort each type's models
        for model_type in models_by_type:
            if model_type != 'Missing from Civitai':
                models_by_type[model_type].sort(key=lambda x: x['downloads'], reverse=True)
            else:
                models_by_type[model_type].sort(key=lambda x: (x['name'] or '').lower())

        # Create sections HTML for each type
        type_sections = ''
        total_models = sum(len(models) for models in models_by_type.values())
        
        for model_type, models in sorted(models_by_type.items()):
            # Create model cards first
            model_cards = []
            for model in models:
                sanitized_base = sanitize_filename(model["base_name"])
                html_name = f"{sanitized_base}.html"
                model_name = (
                    f'<a href="{sanitized_base}/{html_name}">{html.escape(model["name"])}</a>'
                    if model.get('has_html', False) or not model.get('missing')
                    else '<span class="missing-model">' + html.escape(model['name']) + '</span>'
                )
                
                dates_section = ''
                if model.get('createdAt', "Unknown") != "Unknown":
                    created_date = model['createdAt'][:10]
                    updated_date = f" | Updated: {model['updatedAt'][:10]}" if model['updatedAt'] != "Unknown" else ''
                    dates_section = f'<div class="dates">Created: {created_date}{updated_date}</div>'
                
                base_model_section = ''
                if model.get('baseModel', 'Unknown') != 'Unknown':
                    base_model_section = f'<div class="base-model">Base Model: {model["baseModel"]}</div>'
                
                downloads_section = ''
                if not model.get('missing'):
                    downloads_section = f'<div class="downloads">Downloads: {model["downloads"]:,}</div>'
                
                filesize_section = ''
                if model.get('file_size'):
                    filesize_section = f'<div class="file-size">Size: {model.get('file_size', 0)/1024:.2f} MB</div>'
                
                trained_words_section = ''
                if model.get('trainedWords'):
                    trained_words_section = f'<div class="trained-words">{", ".join(model["trainedWords"])}</div>'
                
                tags_html = ''.join(f'<span class="tag">{tag}</span>' for tag in model['tags'])
                
                sanitized_base_name = sanitize_filename(model['base_name'])
                preview_path = f"{sanitized_base_name}/{sanitized_base_name}_preview_0.jpeg"
                
                card_html = f"""
                    <div class="model-card{' missing' if model.get('missing') else ''}{' processed' if model.get('has_html') else ''}" 
                    data-tags="{','.join(model['tags']).lower()}"
                    data-name="{(model['name'] or '').lower()}"
                    data-creator="{(model['creator'] or '').lower()}"
                    data-downloads="{model['downloads']}"
                    data-filename="{model['base_name'].lower()}"
                    data-raw-size="{model.get('file_size', 0)}"
                    data-added-date="{model.get('added_date', '')}">
                        <img class="model-cover" src="{preview_path}" onerror="if (this.src.includes('preview_0')) {{ this.src = this.src.replace('preview_0', 'preview_1'); }} else {{ this.style.display='none'; }}" loading="lazy">
                        <h3>{model_name}</h3>
                        <small class="version-name">{model.get('version_name', '')}</small>
                        <div>by {model['creator']}</div>
                        {base_model_section}
                        {downloads_section}
                        {filesize_section}
                        {dates_section}
                        <div class="tags">
                            {tags_html}
                        </div>
                        {trained_words_section}
                    </div>
                """
                model_cards.append(card_html)

            # Create section with all model cards
            type_sections += f"""
                <div class="type-section" data-type="{model_type.lower()}">
                    <h2>{model_type} ({len(models)} models)</h2>
                    <div class="models-grid">
                        {''.join(model_cards)}
                    </div>
                </div>
            """

        # Update the HTML content with type sections
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Civitai Data Manager</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            font-size: 0.8rem;
            color: #666;
        }}
        .search-container {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .controls {{
            display: flex;
            gap: 10px;
            justify-content: center;
            align-items: center;
            flex-wrap: wrap;
            margin: 20px 0;
        }}
        .search-box {{
            width: 400px;
            padding: 10px;
            font-size: 16px;
            border: 2px solid #ddd;
            border-radius: 4px;
        }}
        .sort-select {{
            padding: 10px;
            font-size: 16px;
            border: 2px solid #ddd;
            border-radius: 4px;
            background-color: white;
            cursor: pointer;
        }}
        .sort-select:hover {{
            border-color: #3498db;
        }}
        .models-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 20px;
        }}
        .model-card {{
            position: relative;
            background-color: #f8f9fa;
            border: 1px solid #eee;
            border-radius: 8px;
            padding: 15px;
            transition: transform 0.2s;
        }}
        .model-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .model-card.processed {{
            min-height: 200px;
        }}
        .model-card.missing {{
            background-color: #fff3f3;
            border: 1px solid #ffcdd2;
        }}
        .model-cover {{
            display: none;
            width: 100%;
            height: 400px;
            object-fit: cover;
            object-position: top;
            border-radius: 8px;
            margin-bottom: 15px;
        }}
        .show-covers .model-cover {{
            display: block;
        }}
        .toggle-button {{
            padding: 14px 16px;
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin: 10px 0;
        }}
        .toggle-button:hover {{
            background-color: #2779af;
        }}
        .toggle-button.active {{
            background-color: #27ae60;
        }}
        .missing-model {{
            color: #d32f2f;
        }}
        .downloads {{
            color: #666;
            font-size: 0.9em;
        }}
        .file-size {{
            color: #666;
            font-size: 0.9em;
            margin-bottom: 10px;
        }}
        .tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
            margin-top: 10px;
        }}
        .tag {{
            background-color: #3498db;
            color: white;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 0.8em;
        }}
        h1 {{
            color: #2c3e50;
        }}
        h3 {{
            margin: 0;
        }}
        .version-name {{
            margin-top: -5px;
            display: block;
        }}
        .hidden {{
            display: none !important;
        }}
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        a:hover {{
            color: #2779af;
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="search-container">
            <h1>Civitai Data Manager</h1>
            <br />
            <h2>({total_models} models)</h2>

            <div class="controls">
                <input type="text" class="search-box" id="searchBox" placeholder="Search by name, filename, or tags (comma separated)...">
                <select id="sortSelect" class="sort-select">
                    <option value="date-desc">Date Added (Newest First)</option>
                    <option value="date-asc">Date Added (Oldest First)</option>
                    <option value="downloads-desc">Downloads (High to Low)</option>
                    <option value="downloads-asc">Downloads (Low to High)</option>
                    <option value="name-asc">Name (A to Z)</option>
                    <option value="name-desc">Name (Z to A)</option>
                    <option value="creator-asc">Creator (A to Z)</option>
                    <option value="creator-desc">Creator (Z to A)</option>
                    <option value="size-asc">File size (Small to Large)</option>
                    <option value="size-desc">File size (Large to Small)</option>
                </select>
                <button id="toggleCovers" class="toggle-button">Show Covers</button>
            </div>
        </div>
        {type_sections}
    </div>

    <div class="footer">
        Civitai Data Manager. Version {__version__}. <a href="https://github.com/jeremysltn/civitai-data-manager">GitHub</a>
        <br />
        Generated: {datetime.now().isoformat()}
    </div>

    <script>
        // Search box
        const searchBox = document.getElementById('searchBox');
        const modelCards = document.querySelectorAll('.model-card');
        const sortSelect = document.getElementById('sortSelect');

        function sortCards() {{
            const [sortKey, sortDir] = sortSelect.value.split('-');
            const sections = document.querySelectorAll('.type-section');
            
            sections.forEach(section => {{
                const cards = Array.from(section.querySelectorAll('.model-card:not(.hidden)'));
                
                cards.sort((a, b) => {{
                    let aVal, bVal;
                    
                    switch(sortKey) {{
                        case 'date':
                            aVal = a.dataset.addedDate || '';
                            bVal = b.dataset.addedDate || '';
                            break;
                        case 'downloads':
                            aVal = parseInt(a.dataset.downloads) || 0;
                            bVal = parseInt(b.dataset.downloads) || 0;
                            break;
                        case 'name':
                            aVal = a.dataset.name || '';
                            bVal = b.dataset.name || '';
                            break;
                        case 'creator':
                            aVal = a.dataset.creator || '';
                            bVal = b.dataset.creator || '';
                            break;
                        case 'size':
                            aVal = parseFloat(a.dataset.rawSize) || 0;
                            bVal = parseFloat(b.dataset.rawSize) || 0;
                            break;
                        default:
                            return 0;
                    }}
                    
                    if (sortDir === 'asc') {{
                        return aVal > bVal ? 1 : -1;
                    }} else {{
                        return aVal < bVal ? 1 : -1;
                    }}
                }});
                
                const grid = section.querySelector('.models-grid');
                cards.forEach(card => grid.appendChild(card));
            }});
        }}

        searchBox.addEventListener('input', function() {{
            const searchTerms = searchBox.value.toLowerCase().split(',').map(term => term.trim()).filter(term => term);
            
            modelCards.forEach(card => {{
                if (!searchTerms.length) {{
                    card.classList.remove('hidden');
                    return;
                }}
                
                const cardTags = card.dataset.tags.split(',');
                const cardName = card.dataset.name;
                const cardFilename = card.dataset.filename;
                
                const matchesSearch = searchTerms.every(searchTerm => 
                    // Check tags
                    cardTags.some(cardTag => cardTag.includes(searchTerm)) ||
                    // Check model name
                    cardName.includes(searchTerm) ||
                    // Check filename
                    cardFilename.includes(searchTerm)
                );
                
                if (matchesSearch) {{
                    card.classList.remove('hidden');
                }} else {{
                    card.classList.add('hidden');
                }}
            }});

            // Show/hide section headers based on visible cards
            document.querySelectorAll('.type-section').forEach(section => {{
                const visibleCards = section.querySelectorAll('.model-card:not(.hidden)').length;
                section.style.display = visibleCards > 0 ? 'block' : 'none';
            }});
            
            // Re-sort visible cards
            sortCards();
        }});

        // Sort functionality
        sortSelect.addEventListener('change', sortCards);
        
        // Load saved sort preference
        const savedSort = localStorage.getItem('sortPreference') || 'date-desc';
        sortSelect.value = savedSort;
        
        // Initial sort
        sortCards();

        // Save sort preference when changed
        sortSelect.addEventListener('change', function() {{
            localStorage.setItem('sortPreference', this.value);
            sortCards();
        }});

        // Image covers toggle
        const toggleButton = document.getElementById('toggleCovers');
        const container = document.querySelector('.container');

        // Check local storage for user preference
        const showCovers = localStorage.getItem('showCovers') === 'true';
        if (showCovers) {{
            container.classList.add('show-covers');
            toggleButton.classList.add('active');
        }}

        toggleButton.addEventListener('click', function() {{
            container.classList.toggle('show-covers');
            this.classList.toggle('active');
            
            // Save preference to local storage
            localStorage.setItem('showCovers', container.classList.contains('show-covers'));
        }});
    </script>
</body>
</html>
"""

        # Write the summary file
        summary_path = Path(output_dir) / 'index.html'
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\nGlobal summary generated: {summary_path}")
        return True

    except Exception as e:
        print(f"Error generating global summary: {str(e)}")
        return False
