from flask import Flask
from products.controllers.product_controller import product_controller
from db.db import db
from flask_cors import CORS

app = Flask(__name__)
app.config.from_object('config.Config')
db.init_app(app)

from consul_service import register_service

# Registrando el blueprint del controlador de productos
app.register_blueprint(product_controller)
CORS(app, supports_credentials=True)

# Endpoint /health y registro automatico en Consul
register_service(app, service_name_default='products', service_port_default=5003, service_host_default='microproducts')

if __name__ == '__main__':
    app.run()
