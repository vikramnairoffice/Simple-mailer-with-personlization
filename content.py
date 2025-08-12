DEFAULT_SUBJECTS = [
    "Notice", "Confirmation","Alert Release","New Update Purchase" ,"New Update Confirmation", "Thank you for contribution", "Thanks for your interest","Maintenance Invoice" ,"Purchase Notification","Maintenance Confirmation",
    "Purchase Confirmation","Purchase Invoice","Immediately notify",'Alert','Update','Hello','Thank You','Thanks','Thanks Again','Notify','Notification','Alert Update','Renewal','Subscription','Activation',"Purchase Report",
    "Purchase Receipt", "New Receipt","Modification in Receipt", "Modification in Invoice", "Thanks for your order","Thanks for your Purchase", "Thanks for your confirmation of renewal", "Thanks for transaction", "New transaction found", "Renewal Transaction Update","Transaction Notification", "Transaction success Alert", "Transaction Activation Update", "Transaction Subscription Notify"
]

DEFAULT_BODIES = [
    "Hello, Please find the attached documents for your review. We appreciate your prompt attention to this matter. Thank you.",
    "Greetings, The files you requested are attached. Please let us know if you have any questions. Best regards.",
    "Dear User, Attached is the information pertaining to your account. Please review it at your earliest convenience. Sincerely.",
]

DEFAULT_GMASS_RECIPIENTS = [
    "recipient1@example.com",
    "recipient2@example.com",
    "recipient3@example.com"
]

PDF_ATTACHMENT_DIR = "./pdfs"
IMAGE_ATTACHMENT_DIR = "./images"
SEND_DELAY_SECONDS = 4.5

SENDER_NAME_TYPES = ["business", "personal"]
DEFAULT_SENDER_NAME_TYPE = "business"

HEADER_LINES = []
ITEMS_ARRAY = []
NOTES_SPINTAX = []
TERMS_SPINTAX = []