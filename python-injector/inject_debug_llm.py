#!/usr/bin/env python3
"""Enhanced debug injection script with modular approach."""

import sys
import pathlib
import logging

# Add the current directory to sys.path for imports
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from config.manager import ConfigManager
from cache.manager import CacheManager
from llm.client import LLMClient
from core.injector import EnhancedCodeInjector  # Use the new enhanced injector
from filesystem.operations import FileSystemManager
from lint.validator import CodeValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
log = logging.getLogger(__name__)

def main():
    if len(sys.argv) != 3:
        print("Usage: python inject_debug_llm.py <service_directory> <service_name>")
        sys.exit(1)
    
    service_path = pathlib.Path(sys.argv[1]).resolve()
    service_name = sys.argv[2]
    
    if not service_path.is_dir():
        log.error(f"❌ Service directory does not exist: {service_path}")
        sys.exit(1)
    
    log.info(f"🚀 Starting enhanced modular debug injection for {service_name}")
    log.info(f"📂 Service directory: {service_path}")
    
    try:
        # Load configuration
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Setup components
        cache_manager = CacheManager(config.get("cache", {}).get("directory", ".debug_cache"))
        debug_vars = set(config.get("debug_vars", ["DEBUG"]))
        
        # Create LLM client
        llm_client = LLMClient(
            provider_name=config["llm"]["provider"],
            config=config["llm"],
            debug_vars=debug_vars
        )
        
        # Create other components
        filesystem_manager = FileSystemManager()
        validator = CodeValidator(llm_client)
        
        # Create enhanced injector
        injector = EnhancedCodeInjector(
            llm_client=llm_client,
            cache_manager=cache_manager,
            validator=validator,
            filesystem_manager=filesystem_manager,
            service_name=service_name
        )
        
        # Get file extensions from config
        file_extensions = config.get("file_extensions", [".go", ".py", ".js", ".java"])
        log.info(f"🔍 Processing files with extensions: {file_extensions}")
        
        # Process using the new modular approach
        processed_count = injector.process_service_files(service_path, file_extensions)
        
        # Show summary
        if hasattr(cache_manager, 'get_cache_stats'):
            cache_stats = cache_manager.get_cache_stats()
            log.info(f"✅ Enhanced modular injection completed for {service_name}")
            log.info(f"📊 Processed {processed_count} files")
            log.info(f"💾 Cache: {cache_stats['files']} files, {cache_stats['total_size_bytes']} bytes")
            log.info(f"🔧 Telemetry version: {cache_stats['telemetry_version']}")
        else:
            log.info(f"✅ Enhanced modular injection completed for {service_name}")
            log.info(f"📊 Processed {processed_count} files")
        
        if processed_count == 0:
            log.warning("⚠️  No files were processed. Check file extensions and directory contents.")
            log.info(f"📁 Files in directory: {list(service_path.glob('*'))}")
    
    except Exception as e:
        log.error(f"❌ Fatal error during injection: {e}")
        import traceback
        log.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
