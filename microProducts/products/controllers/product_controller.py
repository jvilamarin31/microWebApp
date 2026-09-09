from flask import Blueprint, request, jsonify
from db.db import db
from products.models.product_model import Products
import os
import time
import threading
import atexit
import requests


product_controller = Blueprint('product_controller', __name__)

# Configuración de Consul
CONSUL_HOST = os.getenv('CONSUL_HOST', 'consul')
CONSUL_PORT = os.getenv('CONSUL_PORT', '8500')
SERVICE_NAME = os.getenv('SERVICE_NAME', 'products')
SERVICE_HOST = os.getenv('SERVICE_HOST', 'microproducts')
SERVICE_PORT = int(os.getenv('SERVICE_PORT', '5003'))
SERVICE_ID = f"{SERVICE_NAME}-{SERVICE_PORT}"


@product_controller.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'service': SERVICE_NAME,
        'host': SERVICE_HOST,
        'port': SERVICE_PORT
    }), 200


def register_in_consul():
    url = f"http://{CONSUL_HOST}:{CONSUL_PORT}/v1/agent/service/register"
    payload = {
        "ID": SERVICE_ID,
        "Name": SERVICE_NAME,
        "Address": SERVICE_HOST,
        "Port": SERVICE_PORT,
        "Check": {
            "HTTP": f"http://{SERVICE_HOST}:{SERVICE_PORT}/health",
            "Interval": "10s",
            "Timeout": "3s",
            "DeregisterCriticalServiceAfter": "24h"
        }
    }
    time.sleep(2)
    registered_once = False
    while True:
        try:
            resp = requests.put(url, json=payload, timeout=3)
            if resp.status_code == 200 and not registered_once:
                print(f"[Consul] Microservicio '{SERVICE_NAME}' registrado exitosamente en Consul ({SERVICE_HOST}:{SERVICE_PORT})")
                registered_once = True
        except Exception:
            pass
        time.sleep(20)


threading.Thread(target=register_in_consul, daemon=True).start()



def product_to_dict(product):
    return {'id': product.id, 'name': product.name,
            'price': float(product.price), 'quantity': product.quantity}


@product_controller.route('/api/products', methods=['GET'])
def get_products():
    print('listado de productos')
    products = Products.query.all()
    result = [product_to_dict(product) for product in products]
    return jsonify(result)


@product_controller.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    print('obteniendo producto')
    product = Products.query.get_or_404(product_id)
    return jsonify(product_to_dict(product))


@product_controller.route('/api/products', methods=['POST'])
def create_product():
    print('creando producto')
    data = request.json
    new_product = Products(name=data['name'], price=data['price'], quantity=data['quantity'])
    db.session.add(new_product)
    db.session.commit()
    return jsonify({'message': 'Product created successfully'}), 201


@product_controller.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    print('actualizando producto')
    product = Products.query.get_or_404(product_id)
    data = request.json
    product.name = data['name']
    product.price = data['price']
    product.quantity = data['quantity']
    db.session.commit()
    return jsonify({'message': 'Product updated successfully'})


@product_controller.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    print('eliminando producto')
    product = Products.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': 'Product deleted successfully'})


# Descuenta del stock la cantidad indicada (usado por microOrders al crear una orden)
@product_controller.route('/api/products/<int:product_id>/decrement', methods=['POST'])
def decrement_product_stock(product_id):
    print('descontando stock del producto', product_id)
    data = request.get_json(silent=True)
    quantity = data.get('quantity') if data else None
    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        return jsonify({'message': 'Cantidad inválida'}), 400
    if quantity <= 0:
        return jsonify({'message': 'Cantidad inválida'}), 400

    product = Products.query.get_or_404(product_id)
    if product.quantity < quantity:
        return jsonify({'message': f'Inventario insuficiente para el producto {product_id}'}), 409
    product.quantity -= quantity
    db.session.commit()
    return jsonify(product_to_dict(product))


# Repone/aumenta el stock en la cantidad indicada (usado por microOrders para rollback)
@product_controller.route('/api/products/<int:product_id>/increment', methods=['POST'])
def increment_product_stock(product_id):
    print('repuniendo stock del producto', product_id)
    data = request.get_json(silent=True)
    quantity = data.get('quantity') if data else None
    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        return jsonify({'message': 'Cantidad inválida'}), 400
    if quantity <= 0:
        return jsonify({'message': 'Cantidad inválida'}), 400

    product = Products.query.get_or_404(product_id)
    product.quantity += quantity
    db.session.commit()
    return jsonify(product_to_dict(product))
