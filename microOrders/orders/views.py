from flask import Flask
import os
from orders.controllers.order_controller import order_controller
from db.db import db
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'secret123')
app.config.from_object('config.Config')
db.init_app(app)

from consul_service import register_service

# Registrando el blueprint del controlador de ordenes
app.register_blueprint(order_controller)
CORS(app, supports_credentials=True)

# Endpoint /health y registro automatico en Consul
register_service(app, service_name_default='orders', service_port_default=5004, service_host_default='microorders')

if __name__ == '__main__':
    app.run()
