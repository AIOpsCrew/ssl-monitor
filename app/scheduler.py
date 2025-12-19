#!/usr/bin/env python3
"""
SSL Certificate Monitor - Scheduler
Runs periodic checks on all monitored websites and sends notifications for expiring certificates
"""

import time
import schedule
import os
import logging
from datetime import datetime
from app.models import load_websites, save_websites
from app.utils import check_certificates

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('ssl_monitor_scheduler')

# Get SNS Topic ARN from environment variable
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', None)

def check_all_certificates():
    """
    Check all websites and send notifications for expiring certificates
    """
    logger.info(f"Starting certificate check at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load websites
    websites = load_websites()
    
    if not websites:
        logger.info("No websites to check")
        return
        
    logger.info(f"Checking {len(websites)} websites")
    
    # Check certificates
    updated_websites = check_certificates(websites, SNS_TOPIC_ARN)
    
    # Save updated website information
    if updated_websites:
        save_websites(updated_websites)
        
    logger.info(f"Certificate check completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    """
    Main scheduler function - runs certificate checks on a schedule
    """
    logger.info("Starting SSL Certificate Monitor Scheduler")
    
    # Schedule certificate checks (daily at 8 AM)
    schedule.every().day.at("08:00").do(check_all_certificates)
    
    # Also run a check immediately on startup
    check_all_certificates()
    
    # Run the scheduler loop
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute for pending scheduled tasks

if __name__ == "__main__":
    main()