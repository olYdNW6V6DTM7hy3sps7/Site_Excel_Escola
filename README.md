# WhatsApp Bulk Contact Manager & Messenger

A privacy-first web application for bulk importing contacts from Excel/CSV files and sending personalized WhatsApp messages through two distinct pathways: VCF file generation and direct Cloud API messaging.

## Features

### 🎯 Core Functionality
- **File Upload**: Support for Excel (.xlsx, .xls) and CSV files
- **AI Column Detection**: Automatic mapping of name and phone columns
- **Phone Number Cleaning**: E.164 format validation with Brazilian format support
- **VCF Generation**: Create contact files for phone import
- **WhatsApp Cloud API**: Direct message sending via Business API
- **Privacy-First**: All processing happens client-side, no data stored on servers

### 🔧 Two Operation Modes
1. **VCF Generation Mode**: 
   - Generate vCard files for bulk contact import
   - Download and import to phone's contact app
   - WhatsApp automatically syncs new contacts

2. **Cloud API Mode**:
   - Send messages directly via WhatsApp Business API
   - Real-time progress tracking
   - Batch processing with rate limiting

### 🛡️ Security Features
- Zero backend storage of contact data
- Client-side encryption for API credentials
- Session-based credential management
- Rate limiting and CORS protection
- GDPR/CCPA compliant architecture

## Quick Start

### 1. Using the Web Application

1. **Upload Your File**:
   - Drag and drop Excel or CSV file
   - Or click to browse files
   - Maximum file size: 10MB

2. **Map Columns**:
   - Use AI detection or manual mapping
   - Select name and phone columns
   - Preview data with validation status

3. **Configure Message**:
   - Create message template with placeholders
   - Preview with first contact data
   - Real-time character counting

4. **Choose Mode**:
   - **VCF Mode**: Generate contact file
   - **API Mode**: Configure WhatsApp Business API credentials

5. **Process Contacts**:
   - Download VCF file or send messages
   - Monitor progress in real-time
   - View success/failure reports

### 2. Setting Up WhatsApp Business API

#### Prerequisites
- Meta Business Account
- WhatsApp Business Account
- Approved phone number
- Valid access token

#### Configuration Steps
1. **Create Meta Business Account**: https://business.facebook.com
2. **Set Up WhatsApp Business Account**: https://developers.facebook.com/apps
3. **Add Phone Number**: Verify and approve your business phone
4. **Create Message Template**: Get template approved by Meta
5. **Generate Access Token**: Create permanent token with required permissions

#### Required Credentials
- **Access Token**: Permanent token from Meta Developer Console
- **Phone Number ID**: Your WhatsApp Business phone number ID
- **Template Name**: Approved message template name
- **Language Code**: Template language (e.g., 'en', 'pt_BR')

## File Format Requirements

### Excel/CSV Structure
Your file should contain at least these columns:
- **Name**: Contact's full name
- **Phone**: Phone number (any format)
- **Optional**: Additional custom fields for personalization

### Supported Formats
- **Excel**: .xlsx, .xls
- **CSV**: Comma-separated values
- **Maximum Size**: 10MB
- **Maximum Contacts**: 10,000 (recommended)

### Phone Number Formats
The system automatically formats phone numbers to E.164 standard:
- **Brazilian**: +55 + DDD + number (e.g., +5511987654321)
- **International**: Automatically detected and corrected
- **Valid Examples**: (11) 98765-4321, 11987654321, +55 11 98765-4321

## API Reference

### Backend Endpoints

#### Health Check
```http
GET /api/health
```
Returns service status and health information.

#### AI Column Detection
```http
POST /api/detect-columns
Content-Type: application/json

{
  "headers": ["Name", "Phone", "Email"],
  "sample_data": [
    {"Name": "John", "Phone": "+1234567890", "Email": "john@example.com"}
  ]
}
```
Returns detected column mappings using AI analysis.

#### Send WhatsApp Messages
```http
POST /api/send-whatsapp-batch
Content-Type: application/json

{
  "contacts": [...],
  "message": "Hello {name}",
  "credentials": {
    "accessToken": "your_token",
    "phoneNumberId": "your_phone_id"
  }
}
```
Sends messages via WhatsApp Cloud API with batch processing.

#### Job Status
```http
GET /api/job-status/{job_id}
```
Returns real-time status of message sending job.

### Rate Limits
- **100 requests per IP per hour**
- **10 messages per second** (WhatsApp API limit)
- **Batch processing** with 1-second delays between batches

## Browser Compatibility

### Supported Browsers
- **Chrome**: 90+
- **Firefox**: 88+
- **Safari**: 14+
- **Edge**: 90+

### Required Features
- JavaScript ES2020+
- File API support
- Local Storage
- Modern CSS Grid/Flexbox

## Development

### Frontend Architecture
- **Framework**: Vanilla JavaScript (ES2020+)
- **Styling**: Tailwind CSS
- **File Parsing**: SheetJS library
- **State Management**: Native JavaScript Proxy/Storage
- **Build Tool**: Vite (optional)

### Backend Architecture
- **Framework**: FastAPI (Python) or Express.js (Node.js)
- **Deployment**: Serverless functions
- **Database**: Redis (optional, for rate limiting)
- **AI Integration**: OpenRouter API proxy

### Local Development
```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Run backend server
uvicorn proxy_server:app --reload --port 8000

# Open frontend
open index.html
```

## Troubleshooting

### Common Issues

#### File Upload Problems
- **Issue**: File not parsing
- **Solution**: Ensure file is valid Excel/CSV format
- **Check**: File size under 10MB limit

#### Phone Number Validation
- **Issue**: Numbers marked as invalid
- **Solution**: Check original format, system auto-corrects most formats
- **Manual**: Edit phone numbers in preview table

#### WhatsApp API Errors
- **Issue**: Messages not sending
- **Solution**: Verify API credentials and template approval
- **Check**: Phone number ID and access token validity

#### AI Detection Failures
- **Issue**: Columns not detected correctly
- **Solution**: Use manual column mapping
- **Fallback**: Heuristic detection available

### Error Messages
- **"Rate limit exceeded"**: Wait and try again later
- **"Invalid file format"**: Use Excel or CSV files only
- **"Missing API credentials"**: Configure WhatsApp Business API settings
- **"Template not approved"**: Check template status in Meta Console

## Privacy & Security

### Data Protection
- **No Storage**: Contact data never stored on servers
- **Client-Side Processing**: All parsing and validation in browser
- **Session Storage**: API credentials stored temporarily
- **Encryption**: Client-side encryption for sensitive data

### Compliance
- **GDPR Ready**: Data processing consent and deletion rights
- **CCPA Compliant**: California privacy regulations
- **WhatsApp Policy**: Business messaging policy compliance
- **Opt-out**: Built-in opt-out mechanisms

## Support

### Documentation
- **User Guide**: Complete walkthrough with screenshots
- **API Reference**: Detailed endpoint documentation
- **Video Tutorials**: Step-by-step video guides
- **FAQ**: Common questions and solutions

### Community
- **GitHub Issues**: Bug reports and feature requests
- **Discussions**: Community support and questions
- **Contributions**: Open source contributions welcome

### Contact
- **Email**: support@whatsapp-bulk-manager.com
- **Website**: https://whatsapp-bulk-manager.com
- **Status Page**: https://status.whatsapp-bulk-manager.com

## License

This project is open source and available under the MIT License. See LICENSE file for details.

## Acknowledgments

- **Meta**: WhatsApp Business API
- **SheetJS**: Excel parsing library
- **Tailwind CSS**: Utility-first CSS framework
- **OpenRouter**: AI model integration
- **Community**: Contributors and testers

---

*Built with ❤️ for privacy-first bulk messaging*