import os
from datetime import datetime
from homeassistant.helpers import service
import glob

DOMAIN = "files"

def setup(hass, config):
    def handle_fetch(call):
        # Normalize the dictionary keys
        normalized_data = {k.lower(): v for k, v in call.data.items()}
        
        directory = normalized_data.get('directory')
        file_name = normalized_data.get('filename')
        extensions = normalized_data.get('extension') or []

        # Validate inputs
        if not isinstance(directory, str) or not isinstance(file_name, str) or not isinstance(extensions, list):
            hass.states.set(f"{DOMAIN}.latest_fetched", "Invalid input")
            return

        if extensions is not None:
            extensions = [ext.lower().strip('.') for ext in extensions]

        files = {ext: [] for ext in extensions}
        try:
            for dirpath, dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    if filename.lower().startswith(file_name.lower()):
                        file_ext = os.path.splitext(filename)[1].lower().strip('.')
                        if extensions is None or file_ext in extensions:
                            files[file_ext].append(os.path.join(dirpath, filename))
        except FileNotFoundError:
            hass.states.set(f"{DOMAIN}.latest_fetched", "Directory not found")
            return
        except NotADirectoryError:
            hass.states.set(f"{DOMAIN}.latest_fetched", "Path is not a directory")
            return
        except PermissionError:
            hass.states.set(f"{DOMAIN}.latest_fetched", "Access denied to directory or a file in the directory")
            return
        except OSError:
            hass.states.set(f"{DOMAIN}.latest_fetched", "Unable to read a file in the directory")
            return

        if not any(files.values()):
            hass.states.set(f"{DOMAIN}.latest_fetched", "No matching files found")
            return

        latest_files = {}
        for ext, ext_files in files.items():
            if ext_files:
                latest_file = max(ext_files, key=os.path.getctime)
                file_type = "file"
                if ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg']:
                    file_type = "image"
                elif ext in ['mp4', 'mkv', 'webm', 'flv', 'vob', 'ogv', 'avi', 'mov', 'wmv']:
                    file_type = "video"
                elif ext in ['mp3', 'flac', 'wav', 'aac', 'ogg', 'wma']:
                    file_type = "music"

                latest_files[file_type] = latest_file

        hass.states.set(f"{DOMAIN}.latest_fetched", "Done", latest_files)


    hass.services.register(DOMAIN, "fetch", handle_fetch)

    return True

