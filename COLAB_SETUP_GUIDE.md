# Google Colab Setup Guide - Simple Mailer Application

This guide provides step-by-step instructions to run the Simple Mailer application in Google Colab.

## Step 1: Open Google Colab

1. Go to [Google Colab](https://colab.research.google.com/)
2. Sign in with your Google account
3. Create a new notebook by clicking **"New notebook"**

## Step 2: Install Application (One Command!)

**Simple Method - Install directly from GitHub:**

```python
# Option 1: Public repository (if public)
!pip install -q git+https://github.com/vikramnairoffice/Simple-mailer-with-personlization.git

# Option 2: Private repository with token
# !pip install -q git+https://vikramnairoffice:YOUR_GITHUB_TOKEN@github.com/vikramnairoffice/Simple-mailer-with-personlization.git

# Install browser for GMass scraping
!playwright install chromium

print("✅ Application and all dependencies installed automatically!")
```

**Alternative Method - Manual Clone:**

```python
# If pip install doesn't work, use manual clone
!git clone https://github.com/vikramnairoffice/Simple-mailer-with-personlization.git
%cd Simple-mailer-with-personlization
!pip install -r requirements.txt
!playwright install chromium
```

## Step 3: Create Required Directories

```python
# Create directories for file uploads and generated content
import os

directories = ['pdfs', 'images', 'generated_invoices', 'gmail_tokens']
for dir_name in directories:
    os.makedirs(dir_name, exist_ok=True)
    print(f"✅ Created directory: {dir_name}")

print("All directories created!")
```

## Step 4: Upload Account Files

Create a new cell to upload your email accounts file:

```python
from google.colab import files
import os

print("Upload your email accounts file (format: email@domain.com,password)")
print("One account per line")

# Upload accounts file
uploaded = files.upload()

# Move to root directory and rename
for filename in uploaded.keys():
    if 'account' in filename.lower() or 'email' in filename.lower():
        os.rename(filename, 'accounts.txt')
        print(f"✅ Accounts file saved as: accounts.txt")
        break

# Verify file content (first 3 lines only for security)
with open('accounts.txt', 'r') as f:
    lines = f.readlines()[:3]
    print(f"\n📧 Found {len(lines)} accounts (showing first 3):")
    for i, line in enumerate(lines, 1):
        email = line.split(',')[0] if ',' in line else line
        print(f"{i}. {email.strip()}")
```

## Step 5: Upload Leads File

```python
print("Upload your leads/recipients file (one email per line)")

# Upload leads file
uploaded = files.upload()

# Move and rename
for filename in uploaded.keys():
    if 'lead' in filename.lower() or 'recipient' in filename.lower():
        os.rename(filename, 'leads.txt')
        print(f"✅ Leads file saved as: leads.txt")
        break

# Verify leads count
with open('leads.txt', 'r') as f:
    leads_count = len(f.readlines())
    print(f"\n📋 Total leads: {leads_count}")
```

## Step 6: Upload Attachment Files (Optional)

```python
print("Upload PDF or image files for attachments (optional)")
print("Skip if you want to use generated invoices only")

# Upload attachments
uploaded = files.upload()

# Organize files by type
for filename in uploaded.keys():
    if filename.lower().endswith(('.pdf')):
        os.rename(filename, f'pdfs/{filename}')
        print(f"✅ PDF saved: pdfs/{filename}")
    elif filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        os.rename(filename, f'images/{filename}')
        print(f"✅ Image saved: images/{filename}")

# List uploaded files
pdf_count = len(os.listdir('pdfs')) if os.path.exists('pdfs') else 0
img_count = len(os.listdir('images')) if os.path.exists('images') else 0
print(f"\n📎 Attachments ready: {pdf_count} PDFs, {img_count} images")
```

## Step 7: Launch the Application

```python
# Method 1: If you used pip install (recommended)
from ui import main
main()

# Method 2: If you used manual clone
# import sys
# sys.path.append('.')
# from ui import gradio_ui
# app = gradio_ui()
# app.launch(share=True, server_name="0.0.0.0", server_port=7860)

# Method 3: Console command (if pip installed)
# !simple-mailer
```

## Step 8: Access the Web Interface

After running Step 7, you'll see output like:
```
Running on local URL:  http://127.0.0.1:7860
Running on public URL: https://abcd1234.gradio.live
```

**Click the public URL** to open the web interface in a new tab.

## Step 9: Configure and Send Emails

### In the Web Interface:

1. **Configuration Tab:**
   - Set email subjects (one per line)
   - Write email body content
   - Configure GMass recipients for testing

2. **Send Emails Tab:**
   - Upload accounts file (if not done in Colab)
   - Upload leads file (if not done in Colab)
   - Select attachment options:
     - Generated invoices (personalized)
     - Random PDFs from uploaded files
     - Random images from uploaded files
   - Set send delay (recommended: 4.5 seconds)

3. **Run GMass Test (Recommended):**
   - Click "Run GMass Test" to analyze deliverability
   - Wait for results table
   - Select high-performing accounts (inbox ≥ 1)

4. **Send Campaign:**
   - Choose selected accounts or all accounts
   - Click "Send Emails"
   - Monitor real-time progress

## Troubleshooting Tips

### Common Issues:

1. **Gradio Interface Not Loading:**
   ```python
   # Restart and try again
   !pip install --upgrade gradio
   ```

2. **Playwright Browser Issues:**
   ```python
   # Reinstall browser
   !playwright install --force chromium
   ```

3. **Gmail API Setup (Optional):**
   ```python
   from google.colab import files
   
   print("Upload Gmail OAuth credentials JSON file:")
   uploaded = files.upload()
   
   for filename in uploaded.keys():
       if filename.endswith('.json'):
           os.rename(filename, 'gmail_credentials.json')
           print("✅ Gmail credentials saved")
   ```

4. **File Permission Issues:**
   ```python
   # Fix permissions
   !chmod -R 755 .
   ```

## Security Notes

- Keep your accounts file secure
- Use app-specific passwords for Gmail accounts
- Don't share the Gradio public URL with others
- Clear sensitive files after use:
  ```python
  # Clean up sensitive files
  !rm -f accounts.txt leads.txt gmail_credentials.json
  !rm -rf gmail_tokens/
  ```

## Sample Files Format

### accounts.txt
```
user1@gmail.com,app_password_here
user2@yahoo.com,regular_password
user3@outlook.com,regular_password
```

### leads.txt
```
recipient1@example.com
recipient2@gmail.com
recipient3@yahoo.com
```

## Next Steps

1. Test with small lead lists first (5-10 emails)
2. Monitor error reports in the interface
3. Use GMass testing to optimize deliverability
4. Scale up gradually for larger campaigns

For detailed feature documentation, see the main README.md file.