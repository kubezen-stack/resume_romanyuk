import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SECRET_KEY = "d7e19042160471160caea8bc50fc5e1adad918417ae2007c6c88118a82147b43"
DEBUG = True

CONTACT_LOG_FILE = os.path.join(BASE_DIR, "logs", "contacts.log")
