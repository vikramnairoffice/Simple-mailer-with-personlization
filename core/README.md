# Simple Mailer with Personalized Attachments

A Python-based email marketing application with GMass deliverability testing integration. Sends personalized emails with dynamic invoice attachments and provides comprehensive deliverability analysis.

## Features

- **Multi-Protocol Email Sending**: Gmail API, Gmail SMTP, Yahoo, Hotmail/Outlook, AOL
- **Personalized Invoice Generation**: Dynamic PDF/image invoices with recipient-specific data
- **GMass Deliverability Testing**: Automated inbox placement analysis and account scoring
- **Multi-Threading**: Concurrent email sending with progress tracking
- **Web Interface**: Gradio-based UI for configuration and monitoring
- **Comprehensive Error Handling**: Advanced error categorization and recovery suggestions

## Quick Start

### Prerequisites
```bash
pip install gradio reportlab pymupdf faker playwright
pip install google-auth-oauthlib google-api-python-client
playwright install chromium
```

### Running the Application
```python
python ui.py
```

Access the web interface at the provided local URL to configure and send emails.

## File Structure

```
├── ui.py                 # Main Gradio web interface
├── mailer.py            # Email sending engine with multi-threading
├── invoice.py           # PDF/image invoice generation
├── gmass_scraper.py     # GMass deliverability testing
├── content.py           # Default content and configuration
├── sender_names.py      # Sender name generation
└── CLAUDE.md           # Development documentation
```

## Usage

1. **Upload Files**: Account credentials and email leads via web interface
2. **Configure**: Set email subjects, bodies, and attachment preferences
3. **Test Deliverability**: Run GMass analysis to identify high-performing accounts
4. **Send Campaign**: Execute email campaign with real-time progress tracking

## Google Colab Optimization

This application is specifically optimized for Google Colab environments with special handling for file operations, networking, and browser automation.

## Gmail API Setup (Optional)

1. Create Google Cloud project and enable Gmail API
2. Download OAuth2 credentials JSON
3. Upload credentials file in the web interface
4. Tokens are automatically managed in `gmail_tokens/` directory

## License

This project is for educational and legitimate marketing purposes only.