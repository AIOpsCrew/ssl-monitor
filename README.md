# SSL Certificate Monitor

A web application to monitor SSL certificate expiration for your websites. Built with Flask, Python, and Docker.

## Features

- Monitor SSL certificates for multiple websites
- Visual indicators for certificate status (green, yellow, red flags)
- View expiration dates and days remaining for each certificate
- AWS SNS integration for expiring certificate notifications
- Docker and Docker Compose support for easy deployment
- Responsive design for desktop and mobile

## Screenshots

(Screenshots will be added once the application is deployed)

## Requirements

- Docker and Docker Compose
- AWS Account (for SNS notifications)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/ssl-certificate-monitor.git
   cd ssl-certificate-monitor
   ```

2. Configure AWS credentials (optional, for SNS notifications):
   - Create an SNS topic in your AWS account
   - Create an IAM user with permissions to publish to SNS
   - Copy the `.env.example` file to `.env` and add your AWS credentials:
     ```
     cp .env.example .env
     ```
   - Edit the `.env` file with your AWS information

3. Build and start the Docker containers:
   ```
   docker-compose up -d
   ```

4. Access the application at http://localhost:5000

## Configuration

You can customize the following settings in the `docker-compose.yml` file or through environment variables:

- `DEBUG`: Set to `True` for development mode
- `SECRET_KEY`: Secret key for Flask session security
- `AWS_REGION`: AWS region for SNS
- `SNS_TOPIC_ARN`: ARN of your AWS SNS topic
- `EXPIRING_THRESHOLD`: Number of days before expiration to show yellow warning (default: 30)

## Usage

### Adding Websites to Monitor

1. Click on "Add Website" in the navigation bar
2. Enter the website URL (domain name or full URL)
3. Optionally, provide a friendly name for the website
4. Click "Add Website"

### Bulk Importing Websites

1. Click on "Bulk Import" in the navigation bar
2. Enter domain names in one of the following formats:
   - One domain per line: `example.com`, `blog.example.com`, etc.
   - Comma-separated list: `example.com,blog.example.com,store.example.com`
   - Paste from a CSV file (first column will be used as the domain name)
3. Click "Import Websites"
4. The domain name will automatically be used as the friendly name

### Checking Certificate Status

- The home page displays all monitored websites with their certificate status
- Green flag: Certificate is valid
- Yellow flag: Certificate is expiring soon (within 30 days by default)
- Red flag: Certificate has expired
- Click "Refresh All" to check all certificates immediately
- Click "Check" next to a specific website to check just that one

### Notifications

If configured with AWS SNS credentials and topic ARN, the application will send notifications when:

- A certificate is expiring soon (yellow status)
- A certificate has expired (red status)

## Scheduled Checks

The application includes a scheduler component that can check certificates daily. To enable it:

1. Uncomment the `scheduler` service in the `docker-compose.yml` file
2. Restart the containers:
   ```
   docker-compose down
   docker-compose up -d
   ```

## Future Enhancements

- [ ] Implement automatic certificate renewal functionality
- [ ] Add email notifications
- [ ] Add user authentication
- [ ] Add support for client certificates
- [ ] Support for certificate chain validation
- [ ] Historical tracking of certificate changes

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.