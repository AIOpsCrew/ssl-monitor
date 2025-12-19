# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SSL Certificate Monitor is a Flask web application that monitors SSL certificate expiration dates for multiple websites. It provides visual status indicators, optional AWS SNS notifications for expiring certificates, and supports Docker deployment.

## Key Commands

### Development
```bash
# Run locally (development)
python run.py

# The app will be available at http://localhost:5000
```

### Docker Deployment
```bash
# Build and start containers
docker-compose up -d

# View logs
docker logs ssl-certificate-monitor

# Stop containers
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

### Scheduler (Optional)
The scheduler service runs daily certificate checks. To enable:
1. Uncomment the `scheduler` service in `docker-compose.yml`
2. Restart: `docker-compose down && docker-compose up -d`

## Architecture

### Data Flow
1. **Storage**: `websites.json` stores all monitored websites with their certificate status
2. **Certificate Checking**: `app/utils.py` handles SSL certificate verification via OpenSSL
3. **Notifications**: AWS SNS integration sends alerts for expiring/expired certificates
4. **Scheduler**: Optional background service runs daily checks at 8 AM

### Core Components

**app/__init__.py**
- Flask application initialization
- Loads configuration from `config.py`

**app/models.py**
- File-based data persistence using `websites.json`
- CRUD operations: `load_websites()`, `save_websites()`, `add_website()`, `remove_website()`, `get_website()`, `update_website()`
- Each website has: `id`, `url`, `name`, `status`, `expiry_date`, `days_remaining`, `added_date`, `related_domains`

**app/utils.py**
- `get_certificate_expiry(hostname)`: Connects to HTTPS endpoint, retrieves SSL cert, calculates days remaining
- `check_certificates(websites, topic_arn)`: Iterates through websites, updates status, sends SNS notifications
- Status values: `"good"`, `"expiring"` (≤30 days), `"expired"` (≤0 days)
- Supports related domains that share the same certificate

**app/routes.py**
- `/`: Home page - displays all websites with certificate status
- `/refresh`: Force refresh all certificates
- `/add`: Add single website (GET/POST)
- `/bulk_import`: Import multiple domains (newline or comma-separated)
- `/check/<id>`: Check specific website certificate
- `/remove/<id>`: Remove website from monitoring
- `/api/websites`: JSON API endpoint for programmatic access
- `/chatbot`: AI Assistant for SSL troubleshooting (GET)
- `/api/chat`: Chatbot API endpoint (POST)

**app/chatbot.py**
- AWS Bedrock integration using Amazon Nova Lite model
- `chat_with_bedrock()`: Sends messages to Bedrock and maintains conversation history
- `get_system_prompt()`: Generates context-aware prompts with errored domain information
- `get_suggested_questions()`: Returns relevant questions based on current errors
- Provides SSL certificate troubleshooting assistance

**app/scheduler.py**
- Standalone process for scheduled certificate checks
- Runs daily at 08:00
- Executes immediate check on startup
- Runs as separate Docker service when enabled

**config.py**
- Environment-based configuration
- Key settings: `SECRET_KEY`, `DEBUG`, `AWS_REGION`, `SNS_TOPIC_ARN`, `EXPIRING_THRESHOLD`

### Certificate Status Logic
- **Green (good)**: More than 30 days until expiration (configurable via `EXPIRING_THRESHOLD`)
- **Yellow (expiring)**: 1-30 days until expiration
- **Red (expired)**: Certificate has expired or invalid

### Related Domains Feature
Websites can have associated `related_domains` that share the same certificate (e.g., www.example.com and example.com). The system:
- Checks certificates for all related domains
- Indicates which domains use the same certificate
- Includes related domain information in SNS notifications

### Environment Variables
Configure via `.env` file or `docker-compose.yml`:
- `SECRET_KEY`: Flask session security (change in production)
- `DEBUG`: Enable Flask debug mode (default: False)
- `AWS_REGION`: AWS region for SNS and Bedrock (default: us-east-1)
- `SNS_TOPIC_ARN`: ARN for SNS notifications (optional)
- `AWS_ACCESS_KEY_ID`: AWS credentials (required for SNS and Bedrock chatbot)
- `AWS_SECRET_ACCESS_KEY`: AWS credentials (required for SNS and Bedrock chatbot)
- `EXPIRING_THRESHOLD`: Days before expiration to trigger warning (default: 30)

**Note**: The AI Assistant chatbot requires AWS Bedrock access with the Nova Lite model enabled in your AWS account.

## Important Implementation Details

### Data Persistence
- All data stored in `data/websites.json` for persistence across container restarts
- Docker mounts `./data:/app/data` volume for persistence
- No database required - simple JSON file storage
- Automatic migration of old `websites.json` from project root to `data/` directory

### Seed File for Initial Setup
The application supports initializing from a `seed_websites.json` file on first boot:

**How it works:**
1. On startup, if `data/websites.json` is empty or doesn't exist, the app loads from `seed_websites.json`
2. Seed data is converted to full website format with IDs, status fields, and timestamps
3. The initialized data is saved to `data/websites.json` for persistence

**Seed file format:**
```json
[
    {
        "url": "https://example.com",
        "name": "Example Domain"
    }
]
```

**Updating the seed file:**
1. Edit `seed_websites.json` in the project root
2. Delete `data/websites.json` (or remove all entries via web UI)
3. Rebuild and restart: `docker-compose up -d --build`
4. The app will reload from the updated seed file

**Generating seed file from Route53:**
```python
import boto3
import json

route53 = boto3.client('route53')
domains = set()

for page in route53.get_paginator('list_hosted_zones').paginate():
    for zone in page.get('HostedZones', []):
        for record_page in route53.get_paginator('list_resource_record_sets').paginate(HostedZoneId=zone['Id']):
            for record in record_page.get('ResourceRecordSets', []):
                if record['Type'] in ['A', 'AAAA'] and not record['Name'].startswith('*'):
                    domains.add(record['Name'].rstrip('.'))

seed_data = [{"url": f"https://{d}", "name": d} for d in sorted(domains)]
print(json.dumps(seed_data, indent=4))
```

### SSL Certificate Checking
- Uses `pyOpenSSL` and `cryptography` libraries
- Connects to port 443, performs TLS handshake
- Extracts certificate, parses expiration date
- 10-second connection timeout to prevent hanging
- Error handling returns `"error"` status for unreachable hosts

### URL Processing
- Automatically prepends `https://` if protocol missing
- Strips protocol and path to extract hostname for SSL checks
- Example: `https://example.com/path` → checks `example.com:443`

### Docker Security
- Runs as non-root user (`appuser`) in container
- Uses gunicorn WSGI server (not Flask dev server)
- Healthcheck endpoint monitors container status

### Bulk Import
- Accepts newline-separated or comma-separated domains
- Basic regex validation: `^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9](?:\.[a-zA-Z]{2,})+`
- Uses domain name as friendly name by default
- Skips duplicates and invalid entries

### AI Assistant (Strands Agent)
- Powered by AWS Strands SDK using Amazon Nova Lite model via Bedrock
- Accessible via "AI Assistant" link in navigation
- **Agentic AI**: Can actually perform diagnostic actions using tools
- Built-in Tools:
  - `check_ssl_certificate()`: Live SSL certificate checking for any domain
  - `dns_lookup()`: DNS resolution and configuration checks
  - `get_errored_domains()`: Query monitored websites with errors
  - `get_domain_status()`: Lookup specific domain in monitoring database
- Features:
  - Real-time SSL diagnostics with actual certificate checks
  - DNS troubleshooting capabilities
  - Database queries for monitoring status
  - Model-driven orchestration for complex troubleshooting workflows
  - Explains errors and provides actionable solutions
- API endpoint: `POST /api/chat` with JSON body `{message, history}`
- Requires AWS credentials with Bedrock permissions
- Uses Strands framework for tool-based agent capabilities

## Testing Certificate Checks

To test certificate functionality without modifying production data:
```python
from app.utils import get_certificate_expiry
expiry_date, status, days_remaining = get_certificate_expiry('google.com')
print(f"Status: {status}, Days: {days_remaining}, Expiry: {expiry_date}")
```
