"""
Chatbot Module - Strands AI Agent for SSL Certificate Troubleshooting
Uses AWS Strands SDK with custom SSL diagnostic tools
"""

import json
import socket
import ssl
import subprocess
from datetime import datetime
from typing import List, Dict
import logging

from strands import Agent, tool
from strands.models import BedrockModel

logger = logging.getLogger(__name__)

# Configure Bedrock model for Strands
BEDROCK_MODEL_ID = "us.amazon.nova-lite-v1:0"
BEDROCK_REGION = "us-east-1"


@tool
def check_ssl_certificate(domain: str) -> dict:
    """
    Check the SSL certificate for a specific domain.

    Args:
        domain: The domain name to check (e.g., 'example.com')

    Returns:
        Dictionary with certificate information including expiry date, issuer, and validity
    """
    try:
        # Remove protocol if present
        domain = domain.replace('https://', '').replace('http://', '').split('/')[0]

        # Create SSL context
        context = ssl.create_default_context()

        # Connect and get certificate
        with socket.create_connection((domain, 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()

                # Parse expiry date
                expiry_str = cert.get('notAfter', '')
                expiry_date = datetime.strptime(expiry_str, '%b %d %H:%M:%S %Y %Z')
                days_remaining = (expiry_date - datetime.now()).days

                # Get issuer
                issuer = dict(x[0] for x in cert.get('issuer', []))

                # Get subject
                subject = dict(x[0] for x in cert.get('subject', []))

                return {
                    "success": True,
                    "domain": domain,
                    "expiry_date": expiry_date.strftime('%Y-%m-%d'),
                    "days_remaining": days_remaining,
                    "issuer": issuer.get('organizationName', 'Unknown'),
                    "subject_cn": subject.get('commonName', domain),
                    "valid": days_remaining > 0
                }

    except socket.gaierror as e:
        return {
            "success": False,
            "domain": domain,
            "error": f"DNS resolution failed: {str(e)}",
            "error_type": "dns"
        }
    except ssl.SSLError as e:
        return {
            "success": False,
            "domain": domain,
            "error": f"SSL handshake failed: {str(e)}",
            "error_type": "ssl"
        }
    except Exception as e:
        return {
            "success": False,
            "domain": domain,
            "error": str(e),
            "error_type": "general"
        }


@tool
def dns_lookup(domain: str) -> dict:
    """
    Perform a DNS lookup for a domain to check DNS configuration.

    Args:
        domain: The domain name to lookup

    Returns:
        Dictionary with DNS records and resolution information
    """
    try:
        # Remove protocol if present
        domain = domain.replace('https://', '').replace('http://', '').split('/')[0]

        # Get A records
        ip_addresses = socket.getaddrinfo(domain, None)
        ips = list(set([addr[4][0] for addr in ip_addresses]))

        # Get canonical name
        try:
            canonical = socket.getfqdn(domain)
        except:
            canonical = domain

        return {
            "success": True,
            "domain": domain,
            "ip_addresses": ips,
            "canonical_name": canonical,
            "resolved": len(ips) > 0
        }

    except socket.gaierror as e:
        return {
            "success": False,
            "domain": domain,
            "error": f"DNS lookup failed: {str(e)}",
            "resolved": False
        }
    except Exception as e:
        return {
            "success": False,
            "domain": domain,
            "error": str(e),
            "resolved": False
        }


@tool
def get_errored_domains() -> List[Dict]:
    """
    Get list of all domains currently showing errors or unknown status in the monitoring system.

    Returns:
        List of domain dictionaries with their error status and details
    """
    try:
        from app.models import load_websites

        websites = load_websites()
        errored = [
            {
                "name": w.get('name'),
                "url": w.get('url'),
                "status": w.get('status'),
                "days_remaining": w.get('days_remaining'),
                "expiry_date": w.get('expiry_date')
            }
            for w in websites
            if w.get('status') not in ['good', 'expiring', 'expired']
        ]

        return errored

    except Exception as e:
        logger.error(f"Error getting errored domains: {str(e)}")
        return []


@tool
def get_domain_status(domain_name: str) -> dict:
    """
    Get the current monitoring status for a specific domain from the database.

    Args:
        domain_name: The domain name to look up

    Returns:
        Dictionary with the domain's current status, expiry date, and monitoring details
    """
    try:
        from app.models import load_websites

        websites = load_websites()

        # Find the domain (case-insensitive search)
        for w in websites:
            if (domain_name.lower() in w.get('name', '').lower() or
                domain_name.lower() in w.get('url', '').lower()):
                return {
                    "found": True,
                    "name": w.get('name'),
                    "url": w.get('url'),
                    "status": w.get('status'),
                    "expiry_date": w.get('expiry_date'),
                    "days_remaining": w.get('days_remaining'),
                    "added_date": w.get('added_date'),
                    "related_domains": w.get('related_domains', [])
                }

        return {"found": False, "error": f"Domain '{domain_name}' not found in monitoring system"}

    except Exception as e:
        return {"found": False, "error": str(e)}


def create_ssl_agent():
    """
    Create and return a Strands AI agent configured with SSL diagnostic tools

    Returns:
        Configured Strands Agent instance
    """
    try:
        # Configure Bedrock model
        model = BedrockModel(
            model_id=BEDROCK_MODEL_ID,
            region=BEDROCK_REGION
        )

        # Create agent with SSL tools
        agent = Agent(
            model=model,
            tools=[
                check_ssl_certificate,
                dns_lookup,
                get_errored_domains,
                get_domain_status
            ],
            system_prompt="""You are an expert SSL/TLS certificate troubleshooting engineer with deep knowledge of PKI, X.509 certificates, TLS handshakes, and DNS infrastructure.
You have access to tools that can check SSL certificates, perform DNS lookups, and query the monitoring database.

CRITICAL: After gathering data with your tools (2-3 tool calls maximum), you MUST provide your analysis and stop. DO NOT call the same tool repeatedly.

When investigating SSL certificate issues, provide HIGHLY TECHNICAL analysis including:
1. Exact error codes and their RFC specifications
2. TLS protocol version details and cipher suite information
3. Certificate chain validation steps (root CA, intermediate CA, leaf certificate)
4. DNS resolution paths including CNAME, A/AAAA records
5. SNI (Server Name Indication) requirements and mismatches
6. Certificate SAN (Subject Alternative Names) vs CN (Common Name) validation
7. OCSP/CRL revocation check failures
8. TCP/IP connection issues vs TLS handshake failures
9. Specific OpenSSL error codes and their meanings
10. Timestamps in UTC with timezone awareness

INVESTIGATION PROTOCOL (Use tools ONCE each, then analyze):
1. Query monitoring database for last known state (get_domain_status)
2. Perform live SSL certificate check ONCE (check_ssl_certificate)
3. Execute DNS lookup ONCE if needed (dns_lookup)
4. Analyze the results and provide your conclusion
5. DO NOT call tools repeatedly - one check per tool is sufficient

OUTPUT FORMAT:
- Use technical terminology without simplification
- Include actual certificate fields (issuer DN, subject DN, serial number, fingerprints)
- Show example commands with full flags and expected output (as suggestions for the user to run manually)
- Reference specific RFCs (RFC 5280 for X.509, RFC 8446 for TLS 1.3, etc.)
- Include exact error messages from socket/SSL libraries
- Provide remediation steps with specific configuration changes

IMPORTANT: You cannot execute shell commands. Provide openssl/dig/curl commands as code examples for the user to run, not as tool calls.
Use code blocks for commands, configuration snippets, and certificate data.
After gathering data with your tools, provide your analysis and STOP."""
        )

        logger.info("Successfully created Strands SSL agent")
        return agent

    except Exception as e:
        logger.error(f"Error creating Strands agent: {str(e)}")
        raise


def chat_with_agent(user_message: str, conversation_history: List[Dict] = None):
    """
    Send a message to the Strands AI agent and get a response

    Args:
        user_message: The user's message
        conversation_history: Previous conversation (not used with Strands, kept for compatibility)

    Returns:
        Dictionary with the agent's response
    """
    try:
        # Create agent
        agent = create_ssl_agent()

        # Run agent with user message
        response = agent(user_message)

        return {
            "message": str(response),
            "error": None
        }

    except Exception as e:
        logger.error(f"Error in chat_with_agent: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

        return {
            "message": None,
            "error": f"Agent error: {str(e)}"
        }


def get_suggested_questions(errored_domains: List[Dict]) -> List[str]:
    """
    Generate suggested questions based on current errored domains

    Args:
        errored_domains: List of websites with errors

    Returns:
        List of suggested question strings
    """
    suggestions = [
        "What domains are currently showing errors?",
        "Check the SSL certificate for 45squared.hr",
        "Why might a DNS lookup fail for a domain?",
        "How can I diagnose SSL handshake failures?",
    ]

    if errored_domains:
        # Add domain-specific suggestions
        for site in errored_domains[:2]:
            domain = site.get('url', '').replace('https://', '').replace('http://', '')
            suggestions.append(f"Investigate the SSL error for {domain}")

    return suggestions
