# CLAUDE.md

## 🚨 GOOGLE COLAB TESTING ENVIRONMENT
**This application is designed and optimized specifically for Google Colab testing and execution only.** All development, testing, and deployment activities should be conducted within Google Colab notebooks. The application has been configured with Colab-specific optimizations for file handling, networking, dependencies, and browser automation.

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a modular Python-based email marketing application with GMass deliverability testing integration. The application sends personalized emails with dynamic invoice attachments and provides comprehensive deliverability analysis through GMass scraping. It supports multi-threading, real-time progress tracking, and both Gmail API and SMTP protocols.

## Architecture

### Core Components

1. **InvoiceGenerator Class** (`invoice.py`) - Generates personalized PDF/image invoices using ReportLab and PyMuPDF
   - Creates random invoice data (company names, addresses, items, pricing) 
   - Personalized account names from recipient email addresses
   - Support for multiple phone numbers on invoices
   - Converts PDFs to high-quality images (135 DPI) for flexible attachment formats
   - Professional styling with payment confirmation messages

2. **SmtpMailer Class** (`mailer.py`) - Multi-protocol email sending with comprehensive error handling
   - Supports Gmail, Yahoo, Hotmail/Outlook, AOL via SMTP
   - Gmail API integration with OAuth2 authentication and token management
   - Multi-threaded sending with worker pools
   - Rate limiting and quota management
   - Attachment support for PDFs and images

3. **Error Tracking System** (`mailer.py`) - Advanced error categorization and reporting
   - AccountErrorTracker class with 12+ error types (AUTH_FAILED, RATE_LIMITED, GMAIL_API_ERROR, etc.)
   - HTML-formatted error reports with timestamp tracking
   - Error solution suggestions and recovery recommendations

4. **Progress Tracking** (`mailer.py`) - Real-time multi-account progress monitoring
   - Per-account progress bars with visual indicators
   - Overall campaign statistics and timing
   - Status tracking (sending, completed, failed)

5. **GMass Deliverability Testing** (`gmass_scraper.py`) - Automated deliverability analysis
   - Playwright-based web scraping of GMass inbox placement results
   - Automated scoring system (inbox + 0.6*promotions)
   - Account selection based on deliverability scores
   - Integration with main sending workflow

6. **Gradio Web Interface** (`ui.py`) - Advanced web UI with multiple tabs
   - Configuration tab for subjects, bodies, and GMass recipients
   - Send emails tab with file uploads and statistics
   - GMass testing integration with results table
   - Real-time progress monitoring and error displays

7. **Content Management** (`content.py`) - Centralized configuration
   - Default subjects, bodies, and GMass recipients
   - Attachment directory configurations
   - Send delay settings

### File Structure
```
mailer.py              # Main email sending engine with multi-threading
invoice.py             # PDF/image invoice generation
ui.py                 # Gradio web interface
gmass_scraper.py      # GMass deliverability testing and scraping
content.py            # Default content and configuration
test_png_generation.py # Invoice generation testing
generated_invoices/   # Generated invoice files (auto-created)
gmail_tokens/         # Gmail OAuth tokens (auto-created)
pdfs/                 # PDF attachments (user-created)
images/               # Image attachments (user-created)
```

## Development Commands

### Running the Application
```python
# Direct execution:
python ui.py

# Or import and run:
from ui import gradio_ui
gradio_ui().launch()
```

### Required Dependencies
```bash
pip install gradio reportlab pymupdf faker playwright
pip install google-auth-oauthlib google-api-python-client  # For Gmail API
playwright install chromium  # For GMass scraping
```

### Gmail API Setup (Optional)
1. Create Google Cloud project and enable Gmail API
2. Download OAuth2 client credentials JSON file
3. Upload credentials file in the UI when using Gmail API mode
4. Tokens will be automatically saved in `gmail_tokens/` directory

## Key Configuration

### Email Account Format
Accounts file should contain: `email@domain.com,password` (one per line)

### Leads File Format  
One email address per line

### Attachment Directories
- `pdfs/` - PDF files for random attachment selection
- `images/` - JPG/PNG files for random attachment selection  
- `generated_invoices/` - Auto-generated personalized invoices

### Operating Modes
1. **Leads Distribution Mode**: Splits leads across accounts evenly
2. **GMass Broadcast Mode**: All accounts send to same recipient list

### Default Settings
- Send delay: 4.5 seconds between emails
- Invoice generation: Personalized with recipient email as account name
- Attachment format: PDF or high-quality PNG (135 DPI)
- Multi-threading: One worker thread per account
- Gmail API: Optional OAuth2 integration for Gmail accounts

## Error Handling

The application includes comprehensive error classification:
- Authentication failures (wrong passwords, app passwords needed)
- Rate limiting and quota issues
- Account suspensions and blocks
- SMTP connection problems
- Gmail API errors and token issues
- Invalid recipients
- Worker thread errors
- GMass scraping failures

Each error type includes specific solutions and recovery suggestions with HTML-formatted reports.

## Testing

### Manual Testing Process
1. Upload test account and leads files via web interface
2. Configure subjects, bodies, and attachment settings
3. Run GMass deliverability test to analyze account quality
4. Select high-performing accounts from deliverability results
5. Execute real send with selected accounts
6. Monitor real-time progress and error tracking

### Test Files
- `test_png_generation.py` - Tests invoice generation functionality
- Use small lead lists (5-10 emails) for initial testing

## GMass Integration

### Deliverability Testing Workflow
1. Run GMass test with all accounts
2. Application sends test emails to GMass recipients
3. GMass scraper fetches inbox placement results
4. Accounts are scored based on deliverability metrics
5. Select high-performing accounts for real campaigns

### Scoring System
- Score = Inbox count + (0.6 × Promotions count)
- Accounts with inbox ≥ 1 are pre-selected
- Results displayed in interactive table with selection checkboxes