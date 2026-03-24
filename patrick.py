#!/usr/bin/env python3
"""
Patrick - AI-Enhanced Development Assistant
Entry point for the Claude-Patrick integration loop
"""

import sys
import os
import signal
import logging
from pathlib import Path
from typing import Optional

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from integration_flow import execute_step
    from claude_interface import ClaudeInterface
    from patrick_developer import PatrickDeveloper
    from reviewer import review_and_enhance_code
    from utils import setup_logging, validate_environment
except ImportError as e:
    print(f"❌ Critical import error: {e}")
    print("Please ensure all required modules are available in the project directory.")
    sys.exit(1)

# Global state for clean shutdown
shutdown_requested = False
logger = None


def display_startup_banner():
    """Display the startup banner showing active components."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    🤖 PATRICK v2.0                          ║
║              AI-Enhanced Development Assistant               ║
╠══════════════════════════════════════════════════════════════╣
║                    ACTIVE COMPONENTS                         ║
║                                                              ║
║  🧠 Claude AI ...................... [ONLINE]               ║
║  👨‍💻 Patrick Developer ................ [ACTIVE]               ║
║  🔄 Integration Flow ................ [ENABLED]              ║
║                                                              ║
║  Status: Ready for development tasks                         ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_requested
    shutdown_requested = True
    if logger:
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    print("\n🛑 Shutdown requested. Finishing current task...")


def validate_startup():
    """Validate that all required components are available."""
    errors = []
    
    # Validate environment
    env_errors = validate_environment()
    if env_errors:
        errors.extend(env_errors)
    
    # Test Claude interface
    try:
        claude = ClaudeInterface()
        if not claude.test_connection():
            errors.append("Claude AI connection test failed")
    except Exception as e:
        errors.append(f"Claude AI initialization failed: {str(e)}")
    
    # Test Patrick Developer
    try:
        patrick = PatrickDeveloper()
        if not patrick.is_available():
            errors.append("Patrick Developer not available")
    except Exception as e:
        errors.append(f"Patrick Developer initialization failed: {str(e)}")
    
    # Check integration flow
    try:
        from integration_flow import IntegrationFlow
        flow = IntegrationFlow()
        if not flow.validate_setup():
            errors.append("Integration Flow validation failed")
    except Exception as e:
        errors.append(f"Integration Flow validation failed: {str(e)}")
    
    return errors


def emergency_fallback_reviewer(code_content: str, context: Optional[str] = None) -> dict:
    """
    Emergency fallback to the original reviewer function.
    Used when the integration flow is unavailable.
    """
    global logger
    if logger:
        logger.warning("Using emergency fallback reviewer")
    
    print("⚠️  Using emergency fallback mode...")
    
    try:
        return review_and_enhance_code(code_content, context)
    except Exception as e:
        if logger:
            logger.error(f"Emergency fallback failed: {str(e)}")
        return {
            'success': False,
            'error': f"Emergency fallback failed: {str(e)}",
            'enhanced_code': code_content,
            'suggestions': [],
            'issues': [f"Both primary and fallback systems failed: {str(e)}"]
        }


def main():
    """Main entry point for Patrick."""
    global logger, shutdown_requested
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Setup logging
        logger = setup_logging()
        logger.info("Starting Patrick v2.0...")
        
        # Display startup banner
        display_startup_banner()
        
        # Validate startup requirements
        print("🔍 Validating system components...")
        startup_errors = validate_startup()
        
        if startup_errors:
            print("❌ Startup validation failed:")
            for error in startup_errors:
                print(f"   • {error}")
            
            response = input("\nWould you like to continue with limited functionality? (y/N): ")
            if response.lower() != 'y':
                logger.error("Startup validation failed, exiting")
                return 1
            
            print("⚠️  Starting in degraded mode...")
            logger.warning("Starting with validation errors present")
        else:
            print("✅ All components validated successfully!")
            logger.info("All components validated successfully")
        
        print("\n🚀 Patrick is ready! Type 'help' for commands or 'exit' to quit.")
        
        # Main interaction loop
        while not shutdown_requested:
            try:
                user_input = input("\nPatrick> ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    break
                
                if user_input.lower() in ['help', '?']:
                    print_help()
                    continue
                
                if user_input.lower() == 'status':
                    print_status()
                    continue
                
                # Process the request through integration flow
                logger.info(f"Processing user request: {user_input[:50]}...")
                
                try:
                    result = execute_step(user_input)
                    
                    if result.get('success', False):
                        print("✅ Task completed successfully!")
                        if result.get('output'):
                            print(f"📄 Output: {result['output']}")
                    else:
                        print(f"❌ Task failed: {result.get('error', 'Unknown error')}")
                        
                        # Offer emergency fallback for code review tasks
                        if 'review' in user_input.lower() or 'enhance' in user_input.lower():
                            fallback_input = input("Would you like to try the emergency fallback reviewer? (y/N): ")
                            if fallback_input.lower() == 'y':
                                fallback_result = emergency_fallback_reviewer(user_input)
                                if fallback_result.get('success'):
                                    print("✅ Emergency fallback completed successfully!")
                                else:
                                    print(f"❌ Emergency fallback also failed: {fallback_result.get('error')}")
                
                except Exception as e:
                    logger.error(f"Integration flow error: {str(e)}")
                    print(f"❌ Integration flow error: {str(e)}")
                    
                    # Offer emergency fallback
                    if 'review' in user_input.lower():
                        fallback_input = input("Would you like to try the emergency fallback? (y/N): ")
                        if fallback_input.lower() == 'y':
                            result = emergency_fallback_reviewer(user_input)
                            if result.get('success'):
                                print("✅ Emergency fallback completed!")
                            else:
                                print(f"❌ Emergency fallback failed: {result.get('error')}")
            
            except KeyboardInterrupt:
                print("\n\n🛑 Interrupt received. Type 'exit' to quit or press Ctrl+C again to force exit.")
                try:
                    # Give user a chance to exit gracefully
                    signal.alarm(3)
                    continue
                except KeyboardInterrupt:
                    break
            except EOFError:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {str(e)}")
                print(f"❌ Unexpected error: {str(e)}")
                continue
        
        # Clean shutdown
        print("\n🔄 Shutting down Patrick...")
        logger.info("Patrick shutdown initiated")
        
        # Cleanup resources
        try:
            # Add any cleanup code here
            pass
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
        
        print("👋 Patrick shutdown complete. Goodbye!")
        logger.info("Patrick shutdown complete")
        return 0
    
    except Exception as e:
        if logger:
            logger.critical(f"Critical error in main: {str(e)}")
        print(f"💥 Critical error: {str(e)}")
        return 1


def print_help():
    """Display help information."""
    help_text = """
📚 PATRICK HELP

Available Commands:
  help, ?          Show this help message
  status           Show system status
  exit, quit, bye  Exit Patrick

Development Tasks:
  • Code review and enhancement
  • File analysis and suggestions
  • Development workflow assistance
  • AI-powered code generation

Examples:
  Patrick> review my_file.py
  Patrick> analyze project structure
  Patrick> help with Python testing
  Patrick> generate a REST API endpoint

🔧 Emergency Mode:
  If the integration flow fails, Patrick can fall back to basic
  reviewer functionality for code analysis tasks.
    """
    print(help_text)


def print_status():
    """Display current system status."""
    print("\n📊 SYSTEM STATUS")
    print("=" * 50)
    
    # Check Claude AI
    try:
        claude = ClaudeInterface()
        claude_status = "🟢 ONLINE" if claude.test_connection() else "🔴 OFFLINE"
    except Exception:
        claude_status = "🔴 ERROR"
    
    # Check Patrick Developer
    try:
        patrick = PatrickDeveloper()
        patrick_status = "🟢 ACTIVE" if patrick.is_available() else "🔴 INACTIVE"
    except Exception:
        patrick_status = "🔴 ERROR"
    
    # Check Integration Flow
    try:
        from integration_flow import IntegrationFlow
        flow = IntegrationFlow()
        flow_status = "🟢 ENABLED" if flow.validate_setup() else "🔴 DISABLED"
    except Exception:
        flow_status = "🔴 ERROR"
    
    print(f"Claude AI: {claude_status}")
    print(f"Patrick Developer: {patrick_status}")
    print(f"Integration Flow: {flow_status}")
    print("=" * 50)


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)