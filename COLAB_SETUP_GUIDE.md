# Google Colab Setup - Simple Mailer

## 1. Install App
```python
!pip install -q git+https://vikramnairoffice:YOUR_TOKEN@github.com/vikramnairoffice/Simple-mailer-with-personlization.git
```

```python
!playwright install chromium
```

## 2. Launch App
```python
!simple-mailer
```

Click the **public URL** (https://xxxxx.gradio.live) that appears.

## 3. Upload Files in Web Interface
- **Accounts file**: `email@gmail.com,password` (one per line)
- **Leads file**: `recipient@email.com` (one per line)

## 4. Send Emails
1. Configure subjects/bodies in **Configuration** tab
2. Go to **Send Emails** tab
3. Upload your files
4. Click **"Send Emails"**

Done! Monitor progress in real-time.

---

## File Formats

**accounts.txt:**
```
user1@gmail.com,app_password
user2@yahoo.com,regular_password
```

**leads.txt:**
```
recipient1@example.com
recipient2@gmail.com
```