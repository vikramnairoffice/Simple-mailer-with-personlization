import random
from faker import Faker

fake = Faker()

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
    "ajaygoel999@gmail.com",
    "test@chromecompete.com", 
    "test@ajaygoel.org",
    "me@dropboxslideshow.com",
    "test@wordzen.com",
    "rajgoel8477@gmail.com",
    "rajanderson8477@gmail.com",
    "rajwilson8477@gmail.com",
    "briansmith8477@gmail.com",
    "oliviasmith8477@gmail.com",
    "ashsmith8477@gmail.com",
    "shellysmith8477@gmail.com",
    "ajay@madsciencekidz.com",
    "ajay2@ctopowered.com",
    "ajay@arena.tec.br",
    "ajay@daustin.co"
]

PDF_ATTACHMENT_DIR = "./pdfs"
IMAGE_ATTACHMENT_DIR = "./images"
SEND_DELAY_SECONDS = 4.5

SENDER_NAME_TYPES = ["business", "personal"]
DEFAULT_SENDER_NAME_TYPE = "business"

BUSINESS_SUFFIXES = [
    "Foundation", "Fdn", "Consulting", "Co", "Services", "Ltd", "Instituto", "Institute", "Corp.",
    "Trustees", "Incorporated", "Technologies", "Assoc.", "Trustee", "Company", "Industries", "LLP",
    "Corp", "Assoc", "Associazione", "Trust", "Solutions", "Group", "Associa", "Corporation",
    "Trusts", "Corpo", "Inc", "PC", "LLC", "Institutes", "Associates"
]

def generate_business_name():
    """Generate business name: FirstName + RandomLetters + BusinessWord + RandomLetters + Suffix"""
    first_name = fake.first_name()
    random_letters_1 = fake.lexify("??").upper()
    business_word = fake.word().capitalize()
    random_letters_2 = fake.lexify("??").upper()
    suffix = random.choice(BUSINESS_SUFFIXES)
    
    return f"{first_name} {random_letters_1} {business_word} {random_letters_2} {suffix}"

def generate_personal_name():
    """Generate personal name: FirstName + RandomTwoLetters"""
    first_name = fake.first_name()
    random_letters = fake.lexify("? ?").upper()
    
    return f"{first_name} {random_letters[0]}. {random_letters[2]}."

def generate_sender_name(name_type="business"):
    """
    Generate sender name based on type
    Args:
        name_type: "business" or "personal"
    Returns:
        Generated sender name string
    """
    if name_type == "business":
        return generate_business_name()
    elif name_type == "personal":
        return generate_personal_name()
    else:
        return generate_business_name()

HEADER_LINES = []
ITEMS_ARRAY = []
NOTES_SPINTAX = []
TERMS_SPINTAX = []