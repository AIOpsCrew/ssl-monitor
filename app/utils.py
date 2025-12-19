import ssl
import socket
import datetime
import boto3
from dateutil import parser
from OpenSSL import SSL
from cryptography import x509
from cryptography.hazmat.backends import default_backend

# Constants for certificate status
STATUS_GOOD = "good"
STATUS_EXPIRING = "expiring"
STATUS_EXPIRED = "expired"

# Configuration for "expiring soon" threshold (in days)
EXPIRING_THRESHOLD = 30

def get_certificate_expiry(hostname):
    """
    Get the expiration date of an SSL certificate for a given hostname.
    
    Args:
        hostname (str): The hostname to check
        
    Returns:
        tuple: (expiry_date, status, days_remaining)
    """
    try:
        # Create an SSL context
        context = SSL.Context(SSL.TLS_CLIENT_METHOD)
        
        # Create a connection
        conn = SSL.Connection(context, socket.socket(socket.AF_INET, socket.SOCK_STREAM))
        conn.settimeout(10)  # Set a timeout
        
        # Connect to the server
        conn.connect((hostname, 443))
        conn.setblocking(1)
        conn.do_handshake()
        
        # Get certificate
        cert = conn.get_peer_certificate()
        
        # Get expiry date
        expiry_date = datetime.datetime.strptime(cert.get_notAfter().decode('ascii'), '%Y%m%d%H%M%SZ')
        
        # Calculate days remaining
        days_remaining = (expiry_date - datetime.datetime.now()).days
        
        # Determine status
        if days_remaining <= 0:
            status = STATUS_EXPIRED
        elif days_remaining <= EXPIRING_THRESHOLD:
            status = STATUS_EXPIRING
        else:
            status = STATUS_GOOD
            
        # Close connection
        conn.close()
        
        return (expiry_date, status, days_remaining)
    
    except Exception as e:
        print(f"Error checking {hostname}: {str(e)}")
        return (None, "error", None)

def send_sns_notification(topic_arn, subject, message):
    """
    Send a notification using AWS SNS
    
    Args:
        topic_arn (str): The ARN of the SNS topic
        subject (str): The subject of the notification
        message (str): The message body
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create SNS client
        sns = boto3.client('sns')
        
        # Publish message
        response = sns.publish(
            TopicArn=topic_arn,
            Subject=subject,
            Message=message
        )
        
        return True
    
    except Exception as e:
        print(f"Error sending SNS notification: {str(e)}")
        return False

def check_certificates(websites, topic_arn=None):
    """
    Check the SSL certificates for a list of websites and send notifications for expiring certificates
    
    Args:
        websites (list): A list of website objects to check
        topic_arn (str): The ARN of the SNS topic for notifications
        
    Returns:
        list: Updated list of website objects with certificate information
    """
    results = []
    
    for website in websites:
        hostname = website.get('url', '').replace('https://', '').replace('http://', '').split('/')[0]
        
        # Skip empty hostnames
        if not hostname:
            continue
            
        # Get certificate info
        expiry_date, status, days_remaining = get_certificate_expiry(hostname)
        
        # Update website object
        website['status'] = status
        website['expiry_date'] = expiry_date.strftime('%Y-%m-%d') if expiry_date else 'Unknown'
        website['days_remaining'] = days_remaining if days_remaining is not None else 'Unknown'
        
        # Check if related domains have the same certificate
        related_domains = website.get('related_domains', [])
        website['related_status'] = []
        
        for related_domain in related_domains:
            related_hostname = related_domain.replace('https://', '').replace('http://', '').split('/')[0]
            
            # Get certificate info for related domain
            related_expiry, related_status, related_days = get_certificate_expiry(related_hostname)
            
            # Record the status
            website['related_status'].append({
                'domain': related_domain,
                'hostname': related_hostname,
                'status': related_status,
                'expiry_date': related_expiry.strftime('%Y-%m-%d') if related_expiry else 'Unknown',
                'days_remaining': related_days if related_days is not None else 'Unknown',
                'same_cert': (
                    expiry_date and related_expiry and 
                    expiry_date.strftime('%Y-%m-%d') == related_expiry.strftime('%Y-%m-%d')
                )
            })
        
        # Send notification if certificate is expiring or expired and notifications are enabled
        if topic_arn and (status == STATUS_EXPIRING or status == STATUS_EXPIRED):
            # Create a message that includes the main domain and any related domains
            related_info = ""
            if related_domains:
                related_info = "\nRelated domains with the same certificate:\n"
                for related in website['related_status']:
                    if related['same_cert']:
                        related_info += f"- {related['hostname']}\n"
            
            subject = f"SSL Certificate Alert: {hostname}"
            message = f"""
            SSL Certificate Alert for {hostname}
            
            Status: {status.upper()}
            Expiry Date: {website['expiry_date']}
            Days Remaining: {days_remaining}
            {related_info}
            Please take action to renew this certificate.
            """
            
            send_sns_notification(topic_arn, subject, message)
            
        results.append(website)
        
    return results