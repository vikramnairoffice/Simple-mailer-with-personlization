# CLAUDE.md

## 🚨 GOOGLE COLAB TESTING ENVIRONMENT
**This application is designed and optimized specifically for Google Colab testing and execution only.** All development, testing, and deployment activities should be conducted within Google Colab notebooks. The application has been configured with Colab-specific optimizations for file handling, networking, dependencies, and browser automation.

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a modular Python-based email marketing application with GMass deliverability testing integration and advanced Gmail API authentication. The application sends personalized emails with dynamic invoice attachments and provides comprehensive deliverability analysis through GMass scraping. It supports multi-threading, real-time progress tracking, and both Gmail API and SMTP protocols with enhanced sender name generation and authentication management.

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
   - Integration with new Gmail authentication system

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

6. **Gmail Authentication System** (`gmail_auth_manager.py`, `gmail_auth_ui.py`) - **NEW ENHANCED SYSTEM**
   - **GmailAuthManager**: Multi-credential OAuth2 authentication management
   - Support for multiple credential files per project
   - Per-account credential mapping and token storage
   - Automatic environment detection (Colab vs Local)
   - Incognito browser launching for secure authentication
   - Token refresh and validation
   - Email auto-discovery from OAuth responses
   - **Gmail Auth UI**: Interactive Gradio interface for authentication
   - Visual authentication status tables with real-time updates
   - One-click authentication buttons with JavaScript integration
   - Quick authentication flow with credential-only authentication
   - Credential file upload and management

7. **Enhanced Content Management** (`content.py`) - **UPDATED WITH SENDER NAMES**
   - Default subjects, bodies, and GMass recipients
   - Attachment directory configurations
   - Send delay settings
   - **Sender Name Generation System**:
     - Business names: FirstName + RandomLetters + BusinessWord + RandomLetters + Suffix
     - Personal names: FirstName + RandomLetters (initials format)
     - Faker library integration for realistic name generation
     - Configurable name types via UI

8. **Gradio Web Interface** (`ui.py`) - **ENHANCED WITH NEW FEATURES**
   - Configuration tab for subjects, bodies, and GMass recipients
   - Send emails tab with file uploads and statistics  
   - **Integrated Gmail authentication interface**
   - GMass testing integration with results table
   - Real-time progress monitoring and error displays
   - **Sender name type selection (business/personal)**
   - **Enhanced Gmail API controls and status**

### File Structure
```
mailer.py                 # Main email sending engine with multi-threading
invoice.py                # PDF/image invoice generation
ui.py                    # Enhanced Gradio web interface with Gmail auth
gmass_scraper.py         # GMass deliverability testing and scraping
content.py               # Content management with sender name generation
gmail_auth_manager.py    # Gmail OAuth2 authentication manager (NEW)
gmail_auth_ui.py         # Gradio UI components for Gmail auth (NEW)  
gmail_auth_js.py         # JavaScript helpers for auth UI (NEW)
setup.py                 # Package installation configuration
requirements.txt         # Python dependencies
test/                    # Test files directory
  ├── test_cleanup.py
  ├── test_distribution.py
  ├── test_gmail_auth.py
  ├── test_gmail_auth_console.py
  └── test_sender_names.py
generated_invoices/      # Generated invoice files (auto-created)
gmail_tokens/           # Gmail OAuth tokens (auto-created)
pdfs/                   # PDF attachments (user-created)
images/                 # Image attachments (user-created)
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
# Core dependencies
pip install gradio reportlab pymupdf faker playwright

# Gmail API support
pip install google-auth-oauthlib google-api-python-client

# Browser automation for GMass scraping
playwright install chromium

# Or install from requirements.txt
pip install -r requirements.txt
```

### Gmail API Setup (Enhanced Authentication System)
1. **Create Google Cloud Project**:
   - Enable Gmail API in Google Cloud Console
   - Create OAuth2 credentials (Desktop Application type)
   - Download credential JSON file(s)

2. **Upload Credentials in Application**:
   - Use the new Gmail authentication interface in the web UI
   - Upload multiple credential JSON files if needed
   - Each project can have separate credentials

3. **Authenticate Accounts**:
   - **Quick Auth**: Select credential file → Click "Authenticate" → Email auto-discovered
   - **Per-Account Auth**: Manual email + credential pairing
   - Authentication opens in incognito browser (local) or shows manual flow (Colab)
   - Tokens automatically saved in `gmail_tokens/` with account-credential mapping

4. **Authentication Features**:
   - Real-time authentication status table
   - One-click re-authentication
   - Multiple credential support per account
   - Automatic token refresh
   - Environment detection (Colab vs Local)

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
- Attachment format: PDF, PNG, or HEIC (135 DPI for images)
- Multi-threading: One worker thread per account
- Gmail API: Enhanced OAuth2 system with multi-credential support
- Sender names: Configurable business/personal name generation
- Authentication: Automatic incognito browser launching

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
Located in `test/` directory:
- `test_distribution.py` - Tests lead distribution algorithms
- `test_gmail_auth.py` - Tests Gmail authentication functionality  
- `test_gmail_auth_console.py` - Console-based Gmail auth testing
- `test_sender_names.py` - Tests sender name generation
- `test_cleanup.py` - Cleanup and maintenance testing
- Use small lead lists (5-10 emails) for initial testing

### Enhanced Testing Process
1. **Authentication Testing**: Use test files to verify Gmail API integration
2. **Sender Name Testing**: Validate business/personal name generation
3. **Distribution Testing**: Verify equal lead distribution with caps
4. **GMass Integration**: Test deliverability scoring and account selection

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

## Recent Enhancements

### Gmail Authentication System (Major Update)
- **Multi-credential support**: Handle multiple OAuth2 credential files
- **Environment auto-detection**: Seamless Colab vs Local environment handling
- **Incognito browser automation**: Secure authentication without polluting browser
- **Real-time status tracking**: Visual authentication status with one-click actions
- **Email auto-discovery**: Authenticate with credential file only, email discovered automatically
- **Enhanced token management**: Per-account per-credential token storage and refresh

### Sender Name Generation (New Feature)
- **Business names**: Realistic company-style names with suffixes (Foundation, Corp, LLC, etc.)
- **Personal names**: Individual-style names with initials
- **Faker integration**: Use Faker library for realistic name generation
- **UI integration**: Configurable sender name types in Gradio interface

### Enhanced UI Features
- **Integrated Gmail authentication interface** with visual status tables
- **Quick authentication workflow** with credential-only flow
- **Improved error handling** and user feedback
- **Real-time authentication status updates**
- **Multi-credential file upload and management**

### Development Environment Improvements
- **Test directory structure** with organized test files
- **Setup.py configuration** for package installation
- **Requirements.txt** for dependency management
- **Enhanced error tracking** and debugging capabilities

## Security Considerations

### Authentication Security
- **Incognito browser usage**: Prevents OAuth token pollution in main browser
- **Token isolation**: Separate token files per account-credential combination
- **Automatic token refresh**: Secure token lifecycle management
- **Environment-specific flows**: Different auth flows for Colab vs Local environments

### Email Security
- **Sender name randomization**: Reduces detection patterns
- **Rate limiting**: Built-in delays to prevent spam classification
- **Error categorization**: Proper handling of authentication and delivery failures
- **Attachment randomization**: Random PDF/image selection for variety