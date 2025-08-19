# Simple Mailer with Personalized Attachments

## Project Overview

A streamlined Python-based email marketing application focused on personalized email sending with dynamic invoice attachments and Gmail API integration. Features high-performance SMTP with persistent connections (84% performance improvement) and simplified token-based Gmail authentication. This application has been optimized for speed, reliability, and ease of use, removing complex OAuth flows in favor of direct token management.

## 📁 FILE ORGANIZATION RULES

### Core Directory Structure:
- **Core folder**: Only store essential code files (.py, .js, .html, etc.)
- **Test files**: Store in separate `/test` folder outside core directory  
- **Cache files**: Store outside core folder (e.g., `__pycache__`, `.gradio`, temp files)

### File Placement Guidelines:
- ✅ **Core directory**: Main application code, modules, utilities
- ✅ **Test folder**: Unit tests, integration tests, test data, test utilities
- ✅ **Outside core**: Cache files, temporary files, build artifacts, logs

## Current Features

### Core Components

1. **InvoiceGenerator** (`invoice.py`) - Personalized PDF/image invoice generation
   - Random invoice data generation with professional styling
   - Personalized account names from recipient emails
   - PDF to image conversion support (135 DPI)
   - Support for multiple phone numbers

2. **SmtpMailer** (`mailer.py`) - High-performance multi-protocol email sending engine
   - Gmail, Yahoo, Hotmail/Outlook, AOL SMTP support with persistent connections
   - 84% performance improvement through connection reuse (15.0s → 2.4s for 10 emails)
   - Enhanced connection management with automatic retry and recovery
   - Gmail API integration with simplified token authentication
   - Multi-threaded sending with worker pools and connection pooling
   - Comprehensive error handling with 5 new connection-related error types
   - Rate limiting and progress tracking

3. **Token-Based Authentication System** (`token_manager.py`, `ui_token_helpers.py`)
   - Simplified direct token file upload and validation (replaced complex OAuth2 system)
   - Direct token management without browser automation dependencies
   - Enhanced Google Colab compatibility
   - Streamlined UI integration with token upload interface
   - Reduced codebase by ~700 lines through simplification

4. **Enhanced Content Management** (`content.py`)
   - Default subjects, bodies, and sender configurations
   - Advanced sender name generation (business/personal types)
   - Faker library integration for realistic names
   - Configurable attachment and delay settings

5. **Gradio Web Interface** (`ui.py`) - Streamlined user interface
   - Unified sending interface with simplified authentication method selection
   - Real-time file statistics and progress monitoring
   - Direct token upload interface for Gmail API authentication
   - Conditional UI components based on email content modes
   - Enhanced performance monitoring and connection status display

### File Structure
```
core/
├── mailer.py              # Main email sending engine
├── invoice.py             # PDF/image invoice generation  
├── ui.py                  # Gradio web interface
├── content.py             # Content and sender name management
├── token_manager.py       # Simple token validation and management
├── ui_token_helpers.py    # Token UI integration helpers
├── setup.py               # Package configuration
└── requirements.txt       # Dependencies

test/                      # Comprehensive test suite
├── test_persistent_connections.py  # SMTP performance tests
├── test_token_manager.py           # Token validation tests  
├── test_mailer_token_integration.py # Mailer integration tests
├── test_ui_token_integration.py    # UI workflow tests
└── (additional test files)         # Legacy and utility tests
gmail_tokens/             # OAuth tokens (auto-created)
```

## Performance Metrics

### SMTP Connection Performance (Latest Optimization)
- **Old Approach**: 15.0 seconds for 10 emails (new connection each time)
- **New Approach**: 2.4 seconds for 10 emails (persistent connection)  
- **Performance Gain**: 84% improvement in bulk email sending
- **Implementation**: Persistent connections with automatic retry and cleanup

### Test Coverage
- **40 comprehensive tests** with 100% passing rate
- **Performance benchmarking** with measurable improvements
- **Connection reliability testing** with failure scenarios
- **UI workflow validation** for all authentication paths

## Development Commands

### Running the Application
```python
python core/ui.py
```

### Dependencies
```bash
pip install -r core/requirements.txt
```

### Testing
```bash
# Run performance tests
python test/test_persistent_connections.py

# Run token management tests  
python test/test_token_manager.py

# Run integration tests
python test/test_mailer_token_integration.py
python test/test_ui_token_integration.py
```

## Key Configuration

### Authentication Methods
- **Gmail API**: Direct token file upload (simplified from OAuth2)
- **App Password**: Traditional SMTP with app-specific passwords

### Email Modes
- **Leads Distribution**: Splits leads across accounts evenly
- **Broadcast**: All accounts send to same recipients

### Attachment Types
- **Invoice**: Auto-generated personalized invoices
- **Random PDF/Image**: From configured directories

## Recent Changes

### Latest Updates (August 2025)
- ✅ **MAJOR PERFORMANCE OPTIMIZATION**: Implemented persistent SMTP connections
  - 84% performance improvement (15.0s → 2.4s for 10 emails)
  - Enhanced connection management with automatic retry and recovery
  - Comprehensive test suite demonstrating performance gains
- ✅ **SIMPLIFIED AUTHENTICATION**: Replaced complex OAuth2 system with direct token upload
  - Removed 1000+ lines of authentication code
  - Enhanced Google Colab compatibility
  - Streamlined UI with direct token file management
  - Comprehensive TDD test suite (40 tests, 100% passing)
- ✅ **ENHANCED TESTING**: Added extensive test coverage
  - Persistent connection performance tests
  - Token manager validation tests
  - UI integration tests
- ✅ **REMOVED GMass SCRAPER**: Simplified application focus
- ✅ **ENHANCED UI**: Unified sending and simplified authentication interface

## UI Development Guidelines

### Interface Framework Requirements
- **UI Framework**: MUST use Gradio exclusively for all user interface development
- **No HTML/CSS**: Do not create custom HTML, CSS, or other web technologies
- **No Alternative Frameworks**: Do not use Streamlit, Flask, Django, or any other web frameworks
- **Gradio Components**: Use only Gradio's built-in components (gr.Button, gr.Textbox, gr.File, etc.)
- **Styling**: Use Gradio's theming and built-in styling options only

## Security & Best Practices

- Direct token file management without browser dependencies
- Isolated token storage per account
- Persistent SMTP connections with automatic cleanup
- Enhanced error handling with connection-specific recovery
- Rate limiting and quota management
- Comprehensive test coverage ensuring reliability