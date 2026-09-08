from flask import Flask, render_template
from users.controllers.user_controller import user_controller
from db.db import db
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = 'secret123'
app.config.from_object('config.Config')
db.init_app(app)

from consul_service import register_service

# Registrando el blueprint del controlador de usuarios
app.register_blueprint(user_controller)
CORS(app, supports_credentials=True)

# Endpoint /health y registro automatico en Consul
register_service(app, service_name_default='users', service_port_default=5002, service_host_default='microusers')

if __name__ == '__main__':
    app.run()
