from flask import render_template, request, redirect, url_for, flash, jsonify
from app import app
from app.models import load_websites, save_websites, add_website, remove_website, get_website, update_website
from app.utils import check_certificates
import os
import re

# Get SNS Topic ARN from environment variable
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', None)

@app.route('/')
def index():
    """
    Home page - display all monitored websites
    """
    websites = load_websites()
    
    # Check certificates for all websites
    websites = check_certificates(websites, SNS_TOPIC_ARN)
    
    # Save updated website information
    save_websites(websites)
    
    return render_template('index.html', websites=websites)

@app.route('/refresh')
def refresh():
    """
    Refresh certificate information for all websites
    """
    websites = load_websites()
    
    # Check certificates for all websites
    websites = check_certificates(websites, SNS_TOPIC_ARN)
    
    # Save updated website information
    save_websites(websites)
    
    return redirect(url_for('index'))

@app.route('/add', methods=['GET', 'POST'])
def add():
    """
    Add a new website to monitor
    """
    if request.method == 'POST':
        url = request.form.get('url', '')
        name = request.form.get('name', '')
        related_domains_text = request.form.get('related_domains', '')
        
        # Validate URL
        if not url:
            flash('URL is required', 'danger')
            return redirect(url_for('add'))
            
        # Add HTTP if not present
        if not url.startswith('http'):
            url = 'https://' + url
        
        # Process related domains
        related_domains = []
        if related_domains_text:
            # Split by comma and clean up
            domains = [d.strip() for d in related_domains_text.split(',')]
            
            # Process each domain
            for domain in domains:
                if domain:
                    # Add HTTPS if not present
                    if not domain.startswith('http'):
                        domain = 'https://' + domain
                    related_domains.append(domain)
            
        # Add website with related domains
        success = add_website(url, name, related_domains)
        
        if success:
            flash('Website added successfully', 'success')
            return redirect(url_for('index'))
        else:
            flash('Website already exists', 'danger')
            return redirect(url_for('add'))
            
    return render_template('add_site.html')

@app.route('/remove/<int:website_id>')
def remove(website_id):
    """
    Remove a website from monitoring
    """
    success = remove_website(website_id)
    
    if success:
        flash('Website removed successfully', 'success')
    else:
        flash('Website not found', 'danger')
        
    return redirect(url_for('index'))

@app.route('/check/<int:website_id>')
def check(website_id):
    """
    Check certificate for a specific website
    """
    website = get_website(website_id)
    
    if website:
        # Check certificate
        websites = check_certificates([website], SNS_TOPIC_ARN)
        
        if websites:
            # Update website information
            update_website(website_id, websites[0])
            flash('Certificate information updated', 'success')
        else:
            flash('Failed to check certificate', 'danger')
    else:
        flash('Website not found', 'danger')
        
    return redirect(url_for('index'))

@app.route('/bulk_import', methods=['GET', 'POST'])
def bulk_import():
    """
    Bulk import websites for monitoring
    """
    if request.method == 'POST':
        domains_text = request.form.get('domains', '')
        
        # Handle both comma-separated and line-by-line input
        if ',' in domains_text:
            domains = [d.strip() for d in domains_text.split(',')]
        else:
            domains = [d.strip() for d in domains_text.splitlines()]
        
        # Filter out empty domains
        domains = [d for d in domains if d]
        
        if not domains:
            flash('No valid domains provided', 'danger')
            return redirect(url_for('bulk_import'))
        
        # Keep track of success and failures
        added_count = 0
        skipped_count = 0
        
        for domain in domains:
            # Basic domain validation
            if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9](?:\.[a-zA-Z]{2,})+', domain):
                skipped_count += 1
                continue
                
            # Format URL with https://
            url = 'https://' + domain
            
            # Use domain as friendly name
            name = domain
            
            # Add website
            success = add_website(url, name)
            
            if success:
                added_count += 1
            else:
                skipped_count += 1
        
        if added_count > 0:
            flash(f'Successfully added {added_count} websites', 'success')
            
        if skipped_count > 0:
            flash(f'Skipped {skipped_count} websites (invalid or already exists)', 'info')
            
        return redirect(url_for('index'))
            
    return render_template('bulk_import.html')

@app.route('/api/websites')
def api_websites():
    """
    API endpoint to get all websites and their certificate information
    """
    websites = load_websites()
    return jsonify(websites)

@app.route('/renew/<int:website_id>')
def renew(website_id):
    """
    Placeholder for certificate renewal functionality
    """
    website = get_website(website_id)

    if website:
        flash('Renewal functionality will be implemented in the future', 'info')
    else:
        flash('Website not found', 'danger')

    return redirect(url_for('index'))

@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    """
    Chatbot interface for SSL certificate troubleshooting
    """
    from app.chatbot import get_suggested_questions

    # Get errored/unknown domains for context
    websites = load_websites()
    errored_domains = [w for w in websites if w.get('status') not in ['good', 'expiring', 'expired']]

    # Get suggested questions
    suggestions = get_suggested_questions(errored_domains)

    return render_template('chatbot.html',
                         errored_domains=errored_domains,
                         suggestions=suggestions)

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """
    API endpoint for Strands AI agent conversations
    """
    from app.chatbot import chat_with_agent

    data = request.get_json()

    if not data or 'message' not in data:
        return jsonify({'error': 'Message is required'}), 400

    user_message = data.get('message', '')
    conversation_history = data.get('history', [])

    # Call Strands agent
    response = chat_with_agent(
        user_message=user_message,
        conversation_history=conversation_history
    )

    if response.get('error'):
        return jsonify({'error': response['error']}), 500

    return jsonify({
        'message': response['message'],
        'history': []  # Strands manages its own conversation state
    })