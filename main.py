"""
OpenClaw Trade Assistant - Main Entry Point
Orchestrates the full lead qualification loop
"""

import time
from datetime import datetime
from config import Config


def main():
    """
    Main loop that:
    1. Polls Gmail every 30 seconds
    2. Detects new leads
    3. Parses lead data
    4. Generates branded reply
    5. Sends reply via Gmail
    6. Stores lead record in Supabase
    """
    print("=" * 60)
    print("OpenClaw Trade Assistant")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Poll interval: {Config.POLL_INTERVAL_SECONDS} seconds")
    print("-" * 60)

    # TODO: Main loop will be implemented in Step 7
    print("⚠ Main loop not yet implemented - complete steps 2-6 first")


if __name__ == "__main__":
    main()
