import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    DEBUG = True
    USERS_SERVICE_URL = os.getenv('USERS_SERVICE_URL', 'http://localhost:5002')
    PRODUCTS_SERVICE_URL = os.getenv('PRODUCTS_SERVICE_URL', 'http://localhost:5003')
    ORDERS_SERVICE_URL = os.getenv('ORDERS_SERVICE_URL', 'http://localhost:5004')
