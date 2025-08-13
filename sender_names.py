import random
from faker import Faker

fake = Faker()

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