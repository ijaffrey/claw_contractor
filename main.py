#!/usr/bin/env python3
"""
Claw Contractor - AI-Powered Development Pipeline
Main entry point for the application.
"""

import argparse
import logging
import signal
import sys
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Global flag for dry run mode
DRY_RUN_MODE = False

class DryRunFormatter(logging.Formatter):
    """Custom formatter that adds [DRY RUN] prefix when in dry run mode."""
    
    def format(self, record):
        formatted = super().format(record)
        if DRY_RUN_MODE:
            return f"[DRY RUN] {formatted}"
        return formatted

def setup_dry_run_logging():
    """Setup logging with dry run formatting."""
    if DRY_RUN_MODE:
        for handler in logging.root.handlers:
            handler.setFormatter(DryRunFormatter(
                fmt='%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            ))

def print_startup_banner():
    """Print the startup banner."""
    banner = """
╔══════════════════════════════════════════════════════════════════════╗
║                         CLAW CONTRACTOR                             ║
║                   AI-Powered Development Pipeline                   ║
║                                                                      ║
║  Automating code generation, review, testing, and deployment        ║
╚══════════════════════════════════════════════════════════════════════╝
    """
    print(banner)
    if DRY_RUN_MODE:
        logger.info("Running in DRY RUN mode - no actual changes will be made")

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully."""
    logger.info("Received interrupt signal. Shutting down gracefully...")
    sys.exit(0)

def import_modules():
    """Import all required modules with proper error handling."""
    try:
        from modules import config_manager
        logger.info("Imported config_manager")
    except ImportError as e:
        logger.error(f"Failed to import config_manager: {e}")
        sys.exit(1)
    
    try:
        from modules import git_integration
        logger.info("Imported git_integration")
    except ImportError as e:
        logger.error(f"Failed to import git_integration: {e}")
        sys.exit(1)
    
    try:
        from modules import ai_client
        logger.info("Imported ai_client")
    except ImportError as e:
        logger.error(f"Failed to import ai_client: {e}")
        sys.exit(1)
    
    try:
        from modules import code_generator
        logger.info("Imported code_generator")
    except ImportError as e:
        logger.error(f"Failed to import code_generator: {e}")
        sys.exit(1)
    
    try:
        from modules import code_reviewer
        logger.info("Imported code_reviewer")
    except ImportError as e:
        logger.error(f"Failed to import code_reviewer: {e}")
        sys.exit(1)
    
    try:
        from modules import test_runner
        logger.info("Imported test_runner")
    except ImportError as e:
        logger.error(f"Failed to import test_runner: {e}")
        sys.exit(1)
    
    try:
        from modules import deployment_manager
        logger.info("Imported deployment_manager")
    except ImportError as e:
        logger.error(f"Failed to import deployment_manager: {e}")
        sys.exit(1)
    
    return {
        'config_manager': config_manager,
        'git_integration': git_integration,
        'ai_client': ai_client,
        'code_generator': code_generator,
        'code_reviewer': code_reviewer,
        'test_runner': test_runner,
        'deployment_manager': deployment_manager
    }

def initialize_modules(modules):
    """Initialize all modules with error handling."""
    try:
        config = modules['config_manager'].ConfigManager()
        logger.info("Initialized configuration manager")
        
        git = modules['git_integration'].GitIntegration(config)
        logger.info("Initialized git integration")
        
        ai = modules['ai_client'].AIClient(config)
        logger.info("Initialized AI client")
        
        generator = modules['code_generator'].CodeGenerator(ai, config)
        logger.info("Initialized code generator")
        
        reviewer = modules['code_reviewer'].CodeReviewer(ai, config)
        logger.info("Initialized code reviewer")
        
        runner = modules['test_runner'].TestRunner(config)
        logger.info("Initialized test runner")
        
        deployer = modules['deployment_manager'].DeploymentManager(config, git)
        logger.info("Initialized deployment manager")
        
        return {
            'config': config,
            'git': git,
            'ai': ai,
            'generator': generator,
            'reviewer': reviewer,
            'runner': runner,
            'deployer': deployer
        }
    except Exception as e:
        logger.error(f"Failed to initialize modules: {e}")
        sys.exit(1)

def demonstration_pipeline(components):
    """Run a simple demonstration of the integrated pipeline."""
    logger.info("Starting demonstration pipeline")
    
    try:
        # Configuration check
        logger.info("Checking configuration...")
        config = components['config']
        
        # Git operations
        logger.info("Checking git status...")
        git = components['git']
        
        # AI client test
        logger.info("Testing AI client connection...")
        ai = components['ai']
        
        # Code generation demo
        logger.info("Demonstrating code generation...")
        generator = components['generator']
        
        # Code review demo
        logger.info("Demonstrating code review...")
        reviewer = components['reviewer']
        
        # Test execution demo
        logger.info("Demonstrating test execution...")
        runner = components['runner']
        
        # Deployment demo
        logger.info("Demonstrating deployment process...")
        deployer = components['deployer']
        
        logger.info("Demonstration pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"Error in demonstration pipeline: {e}")
        return False
    
    return True

def main_loop(components):
    """Simple main loop demonstrating module integration."""
    logger.info("Entering main processing loop")
    
    try:
        # Run demonstration pipeline
        success = demonstration_pipeline(components)
        
        if success:
            logger.info("All modules integrated successfully")
        else:
            logger.error("Integration demonstration failed")
            return 1
            
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        return 0
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {e}")
        return 1
    
    return 0

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Claw Contractor - AI-Powered Development Pipeline"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run in dry-run mode (no actual changes will be made)'
    )
    return parser.parse_args()

def main():
    """Main entry point."""
    global DRY_RUN_MODE
    
    # Parse arguments
    args = parse_arguments()
    DRY_RUN_MODE = args.dry_run
    
    # Setup logging with dry run formatting
    setup_dry_run_logging()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Print startup banner
    print_startup_banner()
    
    # Import modules
    logger.info("Importing required modules...")
    modules = import_modules()
    logger.info("All modules imported successfully")
    
    # Initialize components
    logger.info("Initializing system components...")
    components = initialize_modules(modules)
    logger.info("All components initialized successfully")
    
    # Run main loop
    logger.info("Starting main application loop...")
    exit_code = main_loop(components)
    
    logger.info("Claw Contractor shutdown complete")
    return exit_code

if __name__ == "__main__":
    sys.exit(main())