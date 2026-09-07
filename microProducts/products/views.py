from flask import Flask
from products.controllers.product_controller import product_controller
from db.db import db
from flask_cors import CORS

app = Flask(__name__)
app.config.from_object('config.Config')
db.init_app(app)

# Registrando el blueprint del controlador de productos
app.register_blueprint(product_controller)
CORS(app, supports_credentials=True)

if __name__ == '__main__':
    app.run()
