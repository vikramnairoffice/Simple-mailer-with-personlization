import random

FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda", "William", "Elizabeth",
    "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Christopher", "Karen",
    "Charles", "Nancy", "Daniel", "Lisa", "Matthew", "Betty", "Anthony", "Helen", "Mark", "Sandra",
    "Donald", "Donna", "Steven", "Carol", "Paul", "Ruth", "Andrew", "Sharon", "Joshua", "Michelle",
    "Kenneth", "Laura", "Kevin", "Sarah", "Brian", "Kimberly", "George", "Deborah", "Edward", "Dorothy",
    "Ronald", "Lisa", "Timothy", "Nancy", "Jason", "Karen", "Jeffrey", "Betty", "Ryan", "Helen",
    "Jacob", "Sandra", "Gary", "Donna", "Nicholas", "Carol", "Eric", "Ruth", "Jonathan", "Sharon",
    "Stephen", "Michelle", "Larry", "Laura", "Justin", "Sarah", "Scott", "Kimberly", "Brandon", "Deborah",
    "Benjamin", "Dorothy", "Samuel", "Amy", "Gregory", "Angela", "Alexander", "Ashley", "Patrick", "Brenda",
    "Frank", "Emma", "Raymond", "Olivia", "Jack", "Cynthia", "Dennis", "Marie", "Jerry", "Janet",
    "Tyler", "Catherine", "Aaron", "Frances", "Jose", "Christine", "Henry", "Samantha", "Adam", "Debra",
    "Douglas", "Rachel", "Nathan", "Carolyn", "Peter", "Virginia", "Zachary", "Martha", "Kyle", "Rebecca"
]

BUSINESS_SUFFIXES = [
    "Foundation", "Fdn", "Consulting", "Co", "Services", "Ltd", "Instituto", "Institute", "Corp.",
    "Trustees", "Incorporated", "Technologies", "Assoc.", "Trustee", "Company", "Industries", "LLP",
    "Corp", "Assoc", "Associazione", "Trust", "Solutions", "Group", "Associa", "Corporation",
    "Trusts", "Corpo", "Inc", "PC", "LLC", "Institutes", "Associates"
]

RANDOM_LETTERS = ["CS", "BT", "AU", "WO", "TF", "KL", "MN", "RT", "PQ", "XY", "ZW", "VU", "ST", "GH", "JK", "DF"]

BUSINESS_WORDS = [
    "Wood", "Steel", "Tech", "Digital", "Global", "Prime", "Elite", "Advanced", "Smart", "Future",
    "Modern", "Royal", "Supreme", "Premier", "First", "Capital", "United", "Central", "National",
    "International", "Universal", "Strategic", "Professional", "Creative", "Innovative", "Dynamic",
    "Optimal", "Superior", "Excellence", "Quality", "Success", "Progress", "Vision", "Leader",
    "Master", "Expert", "Secure", "Reliable", "Trusted", "Proven", "Effective", "Efficient"
]

def generate_business_name():
    """Generate business name: FirstName + RandomLetters + BusinessWord + RandomLetters + Suffix"""
    first_name = random.choice(FIRST_NAMES)
    random_letters_1 = random.choice(RANDOM_LETTERS)
    business_word = random.choice(BUSINESS_WORDS)
    random_letters_2 = random.choice(RANDOM_LETTERS)
    suffix = random.choice(BUSINESS_SUFFIXES)
    
    return f"{first_name} {random_letters_1} {business_word} {random_letters_2} {suffix}"

def generate_personal_name():
    """Generate personal name: FirstName + RandomTwoLetters"""
    first_name = random.choice(FIRST_NAMES)
    letter1 = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    letter2 = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    
    return f"{first_name} {letter1}. {letter2}."

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