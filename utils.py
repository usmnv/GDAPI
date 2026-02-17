import random
import string

def generate_customer_code():
    return "GD-" + "".join(random.choices(string.digits, k=4))