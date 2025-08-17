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

6. **Gmail Authentication System** (`gmail_auth_manager.py`, `gmail_auth_ui.py`, `gmail_auth_js.py`) - **ENHANCED MULTI-FILE SYSTEM**
   - **GmailAuthManager**: Complete OAuth2 authentication lifecycle management
     - Multi-credential file support with project-level organization
     - Per-account credential mapping and isolated token storage
     - Environment auto-detection (Google Colab vs Local environments)
     - Advanced incognito browser launching with Windows/Mac/Linux support
     - Automatic token refresh and validation with error recovery
     - Email auto-discovery from OAuth responses for streamlined authentication
     - HTTP callback server for secure local authentication flows
   - **Gmail Auth UI**: Interactive Gradio interface with advanced features
     - Real-time authentication status tables with visual indicators
     - One-click authentication buttons with JavaScript integration
     - Quick authentication flow supporting credential-only authentication
     - Multiple credential file upload and management interface
     - Dynamic credential dropdown updates and selection
   - **Gmail Auth JS**: JavaScript integration layer for enhanced interactivity
     - Dynamic button event handling for authentication triggers
     - Automatic Gradio component discovery and interaction
     - Real-time UI updates and status synchronization
     - Cross-browser compatibility for authentication flows

7. **Enhanced Content Management** (`content.py`) - **COMPREHENSIVE CONTENT SYSTEM**
   - Extensive default subjects and bodies for email campaigns
   - Default GMass recipients list for testing campaigns
   - Attachment directory configurations for PDFs and images
   - Configurable send delay settings for rate limiting
   - **Advanced Sender Name Generation System**:
     - Business names: FirstName + RandomLetters + BusinessWord + RandomLetters + Suffix
     - Personal names: FirstName + RandomLetters (initials format) 
     - Faker library integration for realistic name generation
     - Comprehensive business suffix database (Foundation, Corp, LLC, etc.)
     - Configurable name types selectable via UI interface

8. **Gradio Web Interface** (`ui.py`) - **FEATURE-RICH USER INTERFACE**
   - Configuration tab for subjects, bodies, and GMass recipients management
   - Send emails tab with file uploads and real-time statistics display
   - **Fully integrated Gmail authentication interface** with status monitoring
   - GMass testing integration with interactive results table and account selection
   - Real-time progress monitoring and comprehensive error displays
   - **Sender name type selection (business/personal)** with live preview
   - **Enhanced Gmail API controls and authentication status**
   - Conditional UI components based on selected email content modes
   - Streamlined attachment and invoice generation interfaces

### File Structure
```
mailer.py                 # Main email sending engine with multi-threading
invoice.py                # PDF/image invoice generation
ui.py                    # Enhanced Gradio web interface with Gmail auth
gmass_scraper.py         # GMass deliverability testing and scraping
content.py               # Content management with sender name generation
gmail_auth_manager.py    # Gmail OAuth2 authentication manager with incognito browser support
gmail_auth_ui.py         # Gradio UI components for Gmail auth with JavaScript integration
gmail_auth_js.py         # JavaScript helpers for auth UI interactions and button handling
setup.py                 # Package installation and distribution configuration
requirements.txt         # Python dependencies
README.md                # Project documentation
ss/                      # Screenshots directory
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
1. **Authentication Testing**: 
   - Use `test_gmail_auth.py` and `test_gmail_auth_console.py` to verify Gmail API integration
   - Test multi-credential file support and environment detection
   - Validate incognito browser launching and OAuth callback handling
2. **Sender Name Testing**: 
   - Use `test_sender_names.py` to validate business/personal name generation
   - Test Faker integration and suffix randomization
3. **Distribution Testing**: 
   - Use `test_distribution.py` to verify equal lead distribution with caps
   - Test different distribution modes and account allocation
4. **GMass Integration**: 
   - Test deliverability scoring and account selection algorithms
   - Validate Playwright-based scraping functionality
5. **Cleanup Testing**:
   - Use `test_cleanup.py` for maintenance and cleanup operations
   - Test token management and file cleanup procedures

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

### Gmail Authentication System (Major Multi-File Update)
- **Advanced Multi-Credential Architecture**: Complete support for multiple OAuth2 credential files per project
- **Intelligent Environment Detection**: Seamless automatic detection and handling of Google Colab vs Local environments
- **Cross-Platform Incognito Browser Automation**: Advanced browser launching with Windows/Mac/Linux support for secure authentication
- **Interactive Real-Time Status Monitoring**: Visual authentication status tables with one-click actions and live updates
- **Email Auto-Discovery Technology**: Authenticate with credential file only - email addresses discovered automatically from OAuth responses
- **Robust Token Management**: Isolated per-account per-credential token storage with automatic refresh and validation
- **HTTP Callback Server Integration**: Secure local authentication flows with automatic callback handling

### JavaScript Integration Layer (New Component)
- **Dynamic UI Interactions**: `gmail_auth_js.py` provides seamless JavaScript integration for authentication workflows
- **Automatic Component Discovery**: Smart detection and interaction with Gradio components for authentication triggers
- **Cross-Browser Event Handling**: Robust event handling for authentication buttons and credential selections
- **Real-Time UI Synchronization**: Live updates and status synchronization across authentication interfaces

### Enhanced Sender Name Generation System
- **Advanced Business Name Generation**: Sophisticated algorithm using FirstName + RandomLetters + BusinessWord + RandomLetters + Suffix patterns
- **Realistic Personal Names**: Individual-style names with professional initial formatting
- **Comprehensive Faker Integration**: Full utilization of Faker library for authentic name generation
- **Extensive Business Suffix Database**: 25+ realistic business suffixes (Foundation, Corp, LLC, Trustees, etc.)
- **Dynamic UI Integration**: Real-time configurable sender name types with preview capabilities

### User Interface Enhancements
- **Streamlined Authentication Interface**: Fully integrated Gmail authentication with visual status monitoring
- **Quick Authentication Workflows**: One-click credential-only authentication with automatic email discovery
- **Enhanced Error Handling**: Comprehensive error feedback and user guidance systems
- **Multi-Credential Management**: Advanced file upload and credential selection interfaces
- **Conditional UI Components**: Dynamic interface elements based on selected email content modes

### Development Infrastructure Improvements
- **Professional Package Configuration**: Complete `setup.py` with proper metadata, entry points, and dependency management
- **Comprehensive Test Suite Organization**: Well-structured test directory with specialized test files for different components
- **Enhanced Documentation**: Detailed inline documentation and comprehensive README structure
- **Robust Dependency Management**: Proper `requirements.txt` with fallback dependency handling

## Security Considerations

### Authentication Security
- **Advanced Incognito Browser Usage**: Comprehensive browser isolation prevents OAuth token pollution in main browser sessions
- **Granular Token Isolation**: Separate token files per unique account-credential combination for maximum security
- **Secure Token Lifecycle Management**: Automatic token refresh with proper error handling and validation
- **Environment-Specific Authentication Flows**: Tailored authentication workflows for Google Colab vs Local environments
- **HTTP Callback Security**: Secure localhost callback server with proper timeout and error handling
- **Credential File Protection**: Safe handling and storage of OAuth2 credential files with proper validation

### Email Security and Deliverability
- **Dynamic Sender Name Randomization**: Advanced patterns to reduce detection and improve deliverability
- **Intelligent Rate Limiting**: Built-in delays and quota management to prevent spam classification
- **Comprehensive Error Categorization**: Proper handling of authentication, delivery, and quota failures
- **Attachment Randomization**: Random PDF/image selection for campaign variety and pattern avoidance
- **Multi-Protocol Support**: SMTP and Gmail API protocols for maximum flexibility and security
- **Account Health Monitoring**: Real-time tracking of account status and deliverability metrics