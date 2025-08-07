"""
Main entry point for the codetective application.
"""

import sys
import argparse
from pathlib import Path

from codetective.interfaces.gui import main as gui_main
from codetective.interfaces.cli import main as cli_main
from codetective.utils.logger import LogLevel, Logger


def main():
    """
    Main entry point that routes to the appropriate interface.
    """
    parser = argparse.ArgumentParser(
        description="Codetective - Multi-Agent Code Review Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Launch GUI interface
  codetective gui
  
  # Use CLI to analyze a project
  codetective cli analyze /path/to/project --agents semgrep trivy
  
  # Discover files in a project
  codetective cli discover /path/to/project
  
  # List available agents
  codetective cli agents
        """
    )
    
    parser.add_argument(
        "interface",
        choices=["gui", "cli"],
        help="Interface to use (gui for Streamlit web interface, cli for command line)"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="codetective 1.0.0"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    # Parse only the interface argument first
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(1)
    
    interface = sys.argv[1]
    
    if interface not in ["gui", "cli"]:
        parser.print_help()
        sys.exit(1)
    
    # Configure logging
    log_level = LogLevel.DEBUG if "--verbose" in sys.argv or "-v" in sys.argv else LogLevel.INFO
    
    logger = Logger.get_logger("main", log_level=log_level)
    logger.info(f"Starting codetective {interface} interface")
    
    try:
        if interface == "gui":
            # Launch Streamlit using subprocess
            import subprocess
            gui_script_path = Path(__file__).parent / "interfaces" / "gui.py"
            streamlit_args = sys.argv[2:]
            command = [sys.executable, "-m", "streamlit", "run", str(gui_script_path)] + streamlit_args
            
            logger.info(f"Running command: {' '.join(command)}")
            subprocess.run(command)
        
        elif interface == "cli":
            # Remove interface argument and pass remaining to CLI
            sys.argv = [sys.argv[0]] + sys.argv[2:]
            cli_main()
    
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    
    except Exception as e:
        logger.error(f"Application failed: {e}")
        if log_level == "DEBUG":
            import traceback
            logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
