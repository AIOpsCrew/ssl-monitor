import json
import os
from datetime import datetime

# Simple file-based storage for websites
# Store websites.json in data directory for persistence across container restarts
DATA_DIR = os.environ.get('DATA_DIR', 'data')
WEBSITES_FILE = os.path.join(DATA_DIR, 'websites.json')
SEED_FILE = 'seed_websites.json'

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

def load_seed_websites():
    """
    Load websites from seed file to initialize the application

    Returns:
        list: List of website dictionaries from seed file
    """
    if not os.path.exists(SEED_FILE):
        return []

    try:
        with open(SEED_FILE, 'r') as f:
            seed_data = json.load(f)

        # Convert seed data to full website format
        websites = []
        for i, item in enumerate(seed_data):
            websites.append({
                'id': i + 1,
                'url': item.get('url', ''),
                'name': item.get('name', item.get('url', '')),
                'status': 'unknown',
                'expiry_date': 'Unknown',
                'days_remaining': 'Unknown',
                'added_date': datetime.now().strftime('%Y-%m-%d'),
                'related_domains': item.get('related_domains', [])
            })

        return websites
    except Exception as e:
        print(f"Error loading seed file: {str(e)}")
        return []

def load_websites():
    """
    Load websites from JSON file
    If websites.json doesn't exist or is empty, load from seed_websites.json

    Returns:
        list: List of website dictionaries
    """
    # Check if websites.json exists and has content
    if os.path.exists(WEBSITES_FILE):
        try:
            with open(WEBSITES_FILE, 'r') as f:
                websites = json.load(f)
                if websites:  # If not empty, return it
                    return websites
        except:
            pass

    # If websites.json doesn't exist or is empty, load from seed file
    print("Loading websites from seed file...")
    seed_websites = load_seed_websites()

    if seed_websites:
        # Save to websites.json for future use
        save_websites(seed_websites)
        print(f"Initialized {len(seed_websites)} websites from seed file")
        return seed_websites

    return []

def save_websites(websites):
    """
    Save websites to JSON file
    
    Args:
        websites (list): List of website dictionaries
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(WEBSITES_FILE, 'w') as f:
            json.dump(websites, f, indent=4)
        return True
    except:
        return False

def add_website(url, name=None, related_domains=None):
    """
    Add a new website to monitor
    
    Args:
        url (str): The URL of the website
        name (str): A friendly name for the website
        related_domains (list): List of related domains that share the same certificate
        
    Returns:
        bool: True if successful, False otherwise
    """
    websites = load_websites()
    
    # Check if website already exists
    for website in websites:
        if website['url'] == url:
            # If the website exists but we're adding related domains, update it
            if related_domains:
                # Get existing related domains or initialize empty list
                existing_related = website.get('related_domains', [])
                
                # Add new related domains that don't already exist
                for domain in related_domains:
                    if domain not in existing_related:
                        existing_related.append(domain)
                        
                # Update the website
                website['related_domains'] = existing_related
                return save_websites(websites)
            return False
            
    # Add new website
    websites.append({
        'id': len(websites) + 1,
        'url': url,
        'name': name or url,
        'status': 'unknown',
        'expiry_date': 'Unknown',
        'days_remaining': 'Unknown',
        'added_date': datetime.now().strftime('%Y-%m-%d'),
        'related_domains': related_domains or []
    })
    
    return save_websites(websites)

def remove_website(website_id):
    """
    Remove a website from monitoring
    
    Args:
        website_id (int): The ID of the website to remove
        
    Returns:
        bool: True if successful, False otherwise
    """
    websites = load_websites()
    
    # Find website by ID
    for i, website in enumerate(websites):
        if website['id'] == int(website_id):
            websites.pop(i)
            return save_websites(websites)
            
    return False

def get_website(website_id):
    """
    Get a specific website by ID
    
    Args:
        website_id (int): The ID of the website to get
        
    Returns:
        dict: Website dictionary or None if not found
    """
    websites = load_websites()
    
    for website in websites:
        if website['id'] == int(website_id):
            return website
            
    return None

def update_website(website_id, data):
    """
    Update a website's information
    
    Args:
        website_id (int): The ID of the website to update
        data (dict): The updated data
        
    Returns:
        bool: True if successful, False otherwise
    """
    websites = load_websites()
    
    for i, website in enumerate(websites):
        if website['id'] == int(website_id):
            websites[i].update(data)
            return save_websites(websites)
            
    return False