# DEBUG: injected by python‑injector
#!/usr/bin/env python3
"""File system operations for debug injection."""

import shutil
import pathlib
import logging

log = logging.getLogger(__name__)

class FileSystemManager:
    @staticmethod
    def copy_go_mod_files(service_dir: pathlib.Path, debug_dir: pathlib.Path):
        """Copy go.mod and go.sum files to debug directory if they exist."""
        for filename in ["go.mod", "go.sum"]:
            src_file = service_dir / filename
            if src_file.is_file():
                dst_file = debug_dir / filename
                shutil.copy2(src_file, dst_file)
                log.debug(f"📋 Copied {filename} to debug directory")
    
    @staticmethod
    def create_debug_directory_structure(service_dir: pathlib.Path) -> pathlib.Path:
        """Create and prepare the debug directory structure."""
        debug_dir = service_dir / "debug"
        debug_dir.mkdir(exist_ok=True)
        
        # Copy Go module files if they exist
        FileSystemManager.copy_go_mod_files(service_dir, debug_dir)
        
        return debug_dir
    
    @staticmethod
    def should_skip_file(file_path: pathlib.Path) -> bool:
        """Determine if a file should be skipped."""
        # Skip files that already have the _debug suffix
        if file_path.stem.endswith("_debug"):
            log.debug(f"Skipping {file_path.name} - already has _debug suffix")
            return True
        
        # Skip files that are already in debug directories
        if "debug" in file_path.parts:
            log.debug(f"Skipping {file_path.name} - in debug directory")
            return True
        
        # Skip hidden files and common non-source files
        if file_path.name.startswith('.'):
            log.debug(f"Skipping {file_path.name} - hidden file")
            return True
        
        # Skip specific file types
        skip_extensions = {'.mod', '.sum', '.md', '.txt', '.yml', '.yaml', '.json'}
        if file_path.suffix.lower() in skip_extensions:
            log.debug(f"Skipping {file_path.name} - excluded extension {file_path.suffix}")
            return True
        
        return False
    
    @staticmethod
    def is_debug_file_up_to_date(src_path: pathlib.Path, debug_path: pathlib.Path) -> bool:
        """Check if debug file is up-to-date compared to source."""
        if not debug_path.is_file():
            return False
        
        # Check modification time
        try:
            if debug_path.stat().st_mtime < src_path.stat().st_mtime:
                log.debug(f"{debug_path.name} is older than source, needs regeneration")
                return False
        except OSError:
            log.debug(f"Could not check timestamps for {debug_path.name}")
            return False
        
        # Check if it contains JSON response instead of code
        try:
            debug_content = debug_path.read_text()
            if debug_content.strip().startswith('{') and '"message":' in debug_content:
                log.debug(f"{debug_path.name} contains JSON response, needs regeneration")
                return False
            
            # Check if file is suspiciously small
            if len(debug_content.strip()) < 100:
                log.debug(f"{debug_path.name} is suspiciously small, needs regeneration")
                return False
                
        except Exception as e:
            log.debug(f"Could not read {debug_path.name}: {e}")
            return False
        
        return True
