import os

# Secret key for session management
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_key')

# Debug mode
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# AWS Settings
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', None)

# Certificate settings
EXPIRING_THRESHOLD = int(os.environ.get('EXPIRING_THRESHOLD', 30))  # Days