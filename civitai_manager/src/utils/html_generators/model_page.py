import json
import html
from ..string_utils import sanitize_filename
from datetime import datetime

def generate_html_summary(output_dir, safetensors_path, VERSION):
    """
    Generate an HTML summary of the model information
    
    Args:
        output_dir (Path): Directory containing the JSON files
        safetensors_path (Path): Path to the safetensors file
        VERSION (str): Version of the script
    """
    try:
        base_name = sanitize_filename(safetensors_path.stem)
        model_path = output_dir / f"{base_name}_civitai_model.json"
        version_path = output_dir / f"{base_name}_civitai_model_version.json"
        hash_path = output_dir / f"{base_name}_hash.json"
        html_path = output_dir / f"{base_name}.html"
        
        # Find all preview images
        preview_images = sorted(output_dir.glob(f"{base_name}_preview*.jpg")) + \
                         sorted(output_dir.glob(f"{base_name}_preview*.jpeg")) + \
                         sorted(output_dir.glob(f"{base_name}_preview*.png")) + \
                         sorted(output_dir.glob(f"{base_name}_preview*.mp4"))

        
        # Check if all required files exist
        if not all(p.exists() for p in [model_path, version_path, hash_path]):
            print("Error: Missing required JSON files for HTML generation")
            return False
            
        # Read JSON data
        try:
            with open(model_path, 'r', encoding='utf-8') as f:
                model_data = json.load(f)
            with open(version_path, 'r', encoding='utf-8') as f:
                version_data = json.load(f)
            with open(hash_path, 'r', encoding='utf-8') as f:
                hash_data = json.load(f)

            # Get stats data
            model_version = next((version for version in model_data["modelVersions"] if version["id"] == version_data.get('id')), None)
            stats = model_version.get('stats', {})
            fileSizeKB = model_version.get('files', [{}])[0].get('sizeKB', None)
            fileSizeMB = fileSizeKB / 1024
            
            # Generate image gallery HTML
            gallery_html = ""
            if preview_images:
                gallery_html = """
                <div class="section">
                    <h2>Preview Images</h2>
                    <div class="gallery">
                """
                for i, img_path in enumerate(preview_images):
                    relative_path = img_path.name
                    json_path = output_dir / f"{img_path.stem}.json"

                    # Load metadata if exists
                    metadata = {}
                    if json_path.exists():
                        try:
                            with open(json_path, 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                        except:
                            pass
                            
                    metadata_attr = f'data-metadata="{html.escape(json.dumps(metadata))}"' if metadata else ''

                    if str(img_path).endswith('.mp4'):
                        gallery_html += f"""
                            <div class="gallery-item" onclick="openModal('{relative_path}', true, this, {i})" {metadata_attr}>
                                <video>
                                    <source src="{relative_path}" type="video/mp4">
                                    Your browser does not support the video tag.
                                </video>
                            </div>
                        """
                    else:
                        gallery_html += f"""
                            <div class="gallery-item" onclick="openModal('{relative_path}', false, this, {i})" {metadata_attr}>
                                <img src="{relative_path}" alt="Preview {i+1}">
                            </div>
                        """
                gallery_html += "</div></div>"
                
            # CSS helpers
            color_map = {
                0: '#27ae60',
                1: '#e93826'
            }
            background_color = color_map.get(model_data.get('nsfw', 'N/A'), '#95a5a6')

            # HTML template
            html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{model_data.get('name', 'Model Information')}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        a:hover {{
            color: #2779af;
            text-decoration: underline;
        }}
        code {{
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.9rem;
            background-color: #ffffff;
            color: #c70066;
            padding: 2px 6px;
            border-radius: 4px;
            border: 1px solid #e1e1e1;
            white-space: pre-wrap;
        }}
        .container {{
            background-color: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .menu {{
            font-size: 0.9rem;
            font-weight: 600;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            font-size: 0.8rem;
            color: #666;
        }}
        .section {{
            margin-bottom: 20px;
            padding-bottom: 20px;
            border-bottom: 1px solid #eee;
        }}
        .section:last-child {{
            border-bottom: none;
        }}
        h1 {{
            color: #2c3e50;
            margin-top: 0;
            margin-bottom: 0;
        }}
        h2 {{
            color: #34495e;
            font-size: 1.4em;
            margin-bottom: 15px;
        }}
        .label {{
            font-weight: bold;
            color: #7f8c8d;
        }}
        .value {{
            margin-bottom: 10px;
        }}
        .description {{
            white-space: pre-wrap;
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            margin: 10px 0;
            overflow: auto;
        }}
        .description img {{
            max-width: 100%;
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
            font-size: 0.9em;
        }}
        .nsfw-level {{
            display: inline-block;
            padding: 5px 10px;
            border-radius: 4px;
            font-weight: bold;
            background-color: {background_color};
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(165px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .stat-card {{
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
            //transition: transform 0.2s;
        }}
        //.stat-card:hover {{
            //transform: translateY(-2px);
            //box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        //}}
        .stat-value {{
            font-size: 1.8em;
            font-weight: bold;
            color: #2c3e50;
            margin: 5px 0;
        }}
        .stat-label {{
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        .rating-bar {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-top: 5px;
        }}
        .likes-ratio {{
            flex-grow: 1;
            height: 8px;
            background-color: #e93826;
            border-radius: 4px;
            overflow: hidden;
        }}
        .likes-fill {{
            height: 100%;
            background-color: #27ae60;
            width: {
                (stats.get('thumbsUpCount', 0) / (stats.get('thumbsUpCount', 0) + stats.get('thumbsDownCount', 0)) * 100) 
                if (stats.get('thumbsUpCount', 0) + stats.get('thumbsDownCount', 0)) > 0 
                else 0
            }%;
        }}
        
        /* New gallery styles */
        .gallery {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .gallery-item {{
            position: relative;
            padding-bottom: 100%;
            cursor: pointer;
            border-radius: 8px;
            overflow: hidden;
            background-color: #f8f9fa;
        }}
        .gallery-item img {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.3s ease;
        }}
        .gallery-item:hover img {{
            transform: scale(1.05);
        }}
        .gallery-item video {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.3s ease;
        }}
        .gallery-item:hover video {{
            transform: scale(1.05);
        }}
        
        /* Modal styles */
        .modal {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.9);
            z-index: 1000;
            overflow: auto;
        }}
        .modal-wrapper {{
            display: flex;
            justify-content: center;
            max-width: 90%;
            max-height: 90%;
            margin: 50px auto;
            overflow: hidden;
        }}
        .modal-content {{
            display: flex;
            max-width: 90%;
            margin: 50px auto;
            background: white;
            border-radius: 8px;
            overflow: hidden;
        }}
        .modal-main {{
            min-width: 0;
            overflow: hidden;
            border-radius: 8px;
        }}
        .modal-main img {{
            display: block;
        }}
        .modal-main video {{
            display: block;
        }}
        .modal-sidebar {{
            width: 300px;
            background: #f8f9fa;
            padding: 20px;
            overflow-y: auto;
            max-height: 90vh;
            border-radius: 8px;
            margin-left: 20px;
        }}
        .metadata-section {{
            margin-bottom: 15px;
        }}
        .metadata-label {{
            font-weight: bold;
            color: #666;
            margin-bottom: 5px;
        }}
        .metadata-value {{
            word-break: break-word;
        }}
        .resource-item {{
            background: #cfcfcf;
            border-radius: 8px;
            padding: 8px;
            font-size: 0.9rem;
            margin-bottom: 5px;
        }}
        .modal-close {{
            position: fixed;
            top: 15px;
            right: 35px;
            color: #f1f1f1;
            font-size: 40px;
            font-weight: bold;
            cursor: pointer;
        }}
        .navigation-hint {{
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            color: #fff;
            background: rgba(0, 0, 0, 0.5);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="menu"><a href="../index.html">Civitai Data Manager</a></div>
            <h1>{model_data.get('name', 'Model Name')}</h1>
            <div><em>{version_data.get('name', 'Version Name')}</em></div>
            <div>by <strong>
                {'<a href="https://civitai.com/user/' + model_data.get('creator', {}).get('username', 'Unknown Creator') + '" target="_blank">' + model_data.get('creator', {}).get('username', 'Unknown Creator') + '</a>' if model_data.get('creator', {}).get('username', 'Unknown Creator') != 'Unknown Creator' else model_data.get('creator', {}).get('username', 'Unknown Creator')}
            </strong></div>
        </div>

        {gallery_html}

        <div class="section">
            <h2>Model Information</h2>
            <div class="label">Type:</div>
            <div class="value">{model_data.get('type', 'N/A')}</div>

            <div class="label">Model ID:</div>
            <div class="value">{model_data.get('id', 'N/A')}</div>

            <div class="label">Version ID:</div>
            <div class="value">{version_data.get('id', 'N/A')}</div>
            
            <!-- <div class="label">NSFW:</div>
            <div class="value">
                <span class="nsfw-level">{model_data.get('nsfw', 'None')}</span>
            </div> -->
            
            <!-- <div class="label">Allow Commercial Use:</div>
            <div class="value">
                {' '.join(f'<span class="tag">{use}</span>' for use in model_data.get('allowCommercialUse', ['N/A']))}
            </div> -->
            
            <div class="label">Description:</div>
            <div class="description">{model_data.get('description', 'No description available')}</div>
            
            <div class="label">Tags:</div>
            <div class="tags">
                {' '.join(f'<span class="tag">{tag}</span>' for tag in model_data.get('tags', []))}
            </div>
        </div>

        <div class="section">
            <h2>Model Statistics</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Downloads</div>
                    <div class="stat-value">{stats.get('downloadCount', 0):,}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Favorites</div>
                    <div class="stat-value">{stats.get('favoriteCount', 0):,}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Comments</div>
                    <div class="stat-value">{stats.get('commentCount', 0):,}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Tips Received</div>
                    <div class="stat-value">{stats.get('tippedAmountCount', 0):,}</div>
                </div>
            </div>
            
            <div style="margin-top: 20px;">
                <div class="label">Rating Distribution</div>
                <div class="rating-bar">
                    <span>👍 {stats.get('thumbsUpCount', 0):,}</span>
                    <div class="likes-ratio">
                        <div class="likes-fill"></div>
                    </div>
                    <span>👎 {stats.get('thumbsDownCount', 0):,}</span>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>Version Information</h2>
            <div class="label">Created At:</div>
            <div class="value">{version_data.get('createdAt', 'N/A')}</div>
            
            <div class="label">Updated At:</div>
            <div class="value">{version_data.get('updatedAt', 'N/A')}</div>
            
            <div class="label">Base Model:</div>
            <div class="value">{version_data.get('baseModel', 'N/A')}</div>

            {'<div class="label">Trained Words:</div><div class="tags"> ' + ' '.join(f'<span class="tag">{word}</span>' for word in version_data.get('trainedWords', [])) + '</div>' if version_data.get('trainedWords') else ''}
        </div>

        <div class="section">
            <h2>File Information</h2>
            <div class="label">Filename:</div>
            <div class="value" style="word-break: break-all;">{base_name}</div>

            <div class="label">SHA256 Hash:</div>
            <div class="value" style="word-break: break-all;">{hash_data.get('hash_value', 'N/A')}</div>

            <div class="label">File size:</div>
            <div class="value" style="word-break: break-all;">{round(fileSizeMB, 2)} MB</div>
        </div>

        <div class="section">
            <h2>Links</h2>
            <div class="value">
                <a href="https://civitai.com/models/{model_data.get('id', '')}" target="_blank">Civitai Model Page</a>
                <br />
                <a href="https://civitai.com/api/download/models/{model_data.get('id', '')}" target="_blank">Civitai Download URL</a>
            </div>
        </div>
    </div>
    
    <div class="footer">
        Civitai Data Manager. Version {VERSION}. <a href="https://github.com/jeremysltn/civitai-data-manager">GitHub</a>
        <br />
        Generated: {datetime.now().isoformat()}
    </div>

    <!-- Modal for full-size media -->
    <div id="imageModal" class="modal">
        <span class="modal-close">&times;</span>
        <div class="modal-wrapper">
            <div class="modal-main">
                <img id="modalImage" style="display: none;">
                <video id="modalVideo" controls style="display: none;">
                    <source src="" type="video/mp4">
                    Your browser does not support the video tag.
                </video>
            </div>
            <div class="modal-sidebar">
                <div id="modalMetadata"></div>
            </div>
        </div>
        <div class="navigation-hint">Use ← → arrow keys to navigate</div>
    </div>

    <script>
        function openModal(mediaPath, isVideo, element, index) {{
            const modal = document.getElementById('imageModal');
            const modalImg = document.getElementById('modalImage');
            const modalVideo = document.getElementById('modalVideo');
            const metadataDiv = document.getElementById('modalMetadata');
            currentImageIndex = index;
            
            modal.style.display = "block";
            
            // Get metadata from clicked element
            const metadata = element.dataset.metadata;
            
            if (isVideo) {{
                modalImg.style.display = "none";
                modalVideo.style.display = "block";
                modalVideo.src = mediaPath;
                modalVideo.play();
            }} else {{
                modalImg.style.display = "block";
                modalVideo.style.display = "none";
                modalImg.src = mediaPath;
            }}
            
            // Display metadata if available
            if (metadata) {{
                const data = JSON.parse(metadata);
                let metadataHtml = '';

                if (data.hasMeta === false) {{
                    metadataHtml += `
                        <p>No metadata available</p>
                    `;
                }}
                
                // Add generation metadata if available
                if (data.meta) {{
                    const meta = data.meta;
                    
                    if (meta.prompt) {{
                        metadataHtml += `
                            <div class="metadata-section">
                                <div class="metadata-label">Prompt</div>
                                <div class="metadata-value" style="white-space: pre-wrap;">${{meta.prompt}}</div>
                            </div>
                        `;
                    }}
                    
                    if (meta.cfgScale) {{
                        metadataHtml += `
                            <div class="metadata-section">
                                <div class="metadata-label">CFG Scale/Guidance</div>
                                <div class="metadata-value">${{meta.cfgScale}}</div>
                            </div>
                        `;
                    }}
                    
                    if (meta.steps) {{
                        metadataHtml += `
                            <div class="metadata-section">
                                <div class="metadata-label">Steps</div>
                                <div class="metadata-value">${{meta.steps}}</div>
                            </div>
                        `;
                    }}
                    
                    if (meta.denoise) {{
                        metadataHtml += `
                            <div class="metadata-section">
                                <div class="metadata-label">Denoise</div>
                                <div class="metadata-value">${{meta.denoise}}</div>
                            </div>
                        `;
                    }}
                    
                    if (meta.seed) {{
                        metadataHtml += `
                            <div class="metadata-section">
                                <div class="metadata-label">Seed</div>
                                <div class="metadata-value">${{meta.seed}}</div>
                            </div>
                        `;
                    }}
                    
                    if (meta.sampler) {{
                        metadataHtml += `
                            <div class="metadata-section">
                                <div class="metadata-label">Sampler</div>
                                <div class="metadata-value">${{meta.sampler}}</div>
                            </div>
                        `;
                    }}
                    
                    if (meta['Schedule type']) {{
                        metadataHtml += `
                            <div class="metadata-section">
                                <div class="metadata-label">Schedule Type</div>
                                <div class="metadata-value">${{meta['Schedule type']}}</div>
                            </div>
                        `;
                    }}
                    
                    if (meta['Distilled CFG Scale']) {{
                        metadataHtml += `
                            <div class="metadata-section">
                                <div class="metadata-label">Distilled CFG Scale</div>
                                <div class="metadata-value">${{meta['Distilled CFG Scale']}}</div>
                            </div>
                        `;
                    }}
                    
                    if (meta.Model) {{
                        metadataHtml += `
                            <div class="metadata-section">
                                <div class="metadata-label">Model</div>
                                <div class="metadata-value">${{meta.Model}}</div>
                            </div>
                        `;
                    }}

                    if (meta['resources'] && meta['resources'].length > 0) {{
                        metadataHtml += `
                            <div class="metadata-section">
                                <div class="metadata-label">Resources</div>
                                <div class="metadata-value">
                                    ${{meta['resources'].map(resource => `
                                        <div class="resource-item">
                                            <div class="resource-name">${{resource.name}} (${{resource.type}})</div>
                                            ${{resource.weight ? `<div class="resource-weight">weight: ${{resource.weight}}</div>` : ''}}
                                        </div>
                                    `).join('')}}
                                </div>
                            </div>
                        `;
                    }}

                    if (meta['additionalResources'] && meta['additionalResources'].length > 0) {{
                        metadataHtml += `
                            <div class="metadata-section">
                                <div class="metadata-label">Additional Resources</div>
                                <div class="metadata-value">
                                    ${{meta['additionalResources'].map(resource => `
                                        <div class="resource-item">
                                            <div class="resource-name">${{resource.name}} (${{resource.type}})</div>
                                            ${{resource.strength ? `<div class="resource-weight">strength: ${{resource.strength}}</div>` : ''}}
                                        </div>
                                    `).join('')}}
                                </div>
                            </div>
                        `;
                    }}
                }}
                
                metadataDiv.innerHTML = metadataHtml;
            }} else {{
                metadataDiv.innerHTML = '<p>No metadata available</p>';
            }}
        }}

        function closeModal() {{
            const modal = document.getElementById('imageModal');
            const modalVideo = document.getElementById('modalVideo');
            modal.style.display = "none";
            modalVideo.pause();
            modalVideo.currentTime = 0;
        }}

        // Close modal
        document.addEventListener('DOMContentLoaded', function() {{
            // Close only when clicking the X button
            document.querySelector('.modal-close').addEventListener('click', function() {{
                closeModal();
            }});

            // Close with Escape key
            document.addEventListener('keydown', function(event) {{
                if (event.key === "Escape") {{
                    closeModal();
                }}
            }});
        }});

        // Track current image index and all gallery items
        let currentImageIndex = 0;
        const galleryItems = document.querySelectorAll('.gallery-item');

        // Initialize gallery items array when DOM loads
        document.addEventListener('DOMContentLoaded', function() {{
            // Add keyboard navigation
            document.addEventListener('keydown', function(event) {{
                const modal = document.getElementById('imageModal');
                // Only handle keyboard navigation when modal is open
                if (modal.style.display === "block") {{
                    switch(event.key) {{
                        case "ArrowLeft":
                            navigateImage(-1);
                            break;
                        case "ArrowRight":
                            navigateImage(1);
                            break;
                        case "Escape":
                            closeModal();
                            break;
                    }}
                }}
            }});
        }});

        // Function to navigate between images
        function navigateImage(direction) {{
            const newIndex = currentImageIndex + direction;
            
            // Check if new index is valid
            if (newIndex >= 0 && newIndex < galleryItems.length) {{
                currentImageIndex = newIndex;
                const nextItem = galleryItems[newIndex];
                
                // Get the media source directly from the gallery item's onclick attribute
                const onclickAttr = nextItem.getAttribute('onclick');
                const mediaPath = onclickAttr.split("'")[1];  // Extract path from onclick="openModal('path',..."
                const isVideo = mediaPath.endsWith('.mp4');
                
                // Use existing openModal function to handle the display and metadata
                openModal(mediaPath, isVideo, nextItem, newIndex);
            }}
        }}
    </script>
</body>
</html>
"""
            # Write HTML file
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            print(f"HTML summary generated: {html_path}")
            return True
                
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON data: {str(e)}")
            return False
            
    except Exception as e:
        print(f"Error generating HTML summary: {str(e)}")
        return False
