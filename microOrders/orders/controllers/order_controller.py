from flask import Blueprint, request, jsonify, session, current_app
from db.db import db
from orders.models.order_model import Order, OrderItem
from decimal import Decimal
import os
import time
import threading
import atexit
import requests


order_controller = Blueprint('order_controller', __name__)

# Configuración de Consul
CONSUL_HOST = os.getenv('CONSUL_HOST', 'consul')
CONSUL_PORT = os.getenv('CONSUL_PORT', '8500')
SERVICE_NAME = os.getenv('SERVICE_NAME', 'orders')
SERVICE_HOST = os.getenv('SERVICE_HOST', 'microorders')
SERVICE_PORT = int(os.getenv('SERVICE_PORT', '5004'))
SERVICE_ID = f"{SERVICE_NAME}-{SERVICE_PORT}"


@order_controller.route('/health', methods=['GET'])
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



def products_service_url():
    """Descubre dinámicamente el servicio de productos a través de Consul."""
    try:
        consul_url = f"http://{CONSUL_HOST}:{CONSUL_PORT}/v1/health/service/products?passing"
        resp = requests.get(consul_url, timeout=3)
        if resp.status_code == 200:
            services = resp.json()
            if services:
                entry = services[0]['Service']
                address = entry.get('Address')
                port = entry.get('Port')
                discovered_url = f"http://{address}:{port}"
                print(f"[Consul Discovery] Servicio 'products' descubierto en {discovered_url}")
                return discovered_url
            else:
                print("[Consul Discovery] Advertencia: No hay instancias de 'products' saludables en Consul.")
    except Exception as e:
        print(f"[Consul Discovery] Error consultando Consul: {e}")

    # Fallback si Consul no está accesible
    fallback = current_app.config.get('PRODUCTS_SERVICE_URL')
    if fallback:
        return fallback.rstrip('/')
    return None


def restore_stock(applied):
    base = products_service_url()
    if not base:
        print('[microOrders] No se pudo resolver URL de productos para restaurar stock')
        return
    for product_id, quantity in reversed(applied):
        try:
            requests.post(f'{base}/api/products/{product_id}/increment',
                          json={'quantity': quantity}, timeout=5)
            print(f'Stock restaurado del producto {product_id}: +{quantity}')
        except requests.exceptions.RequestException as e:
            print(f'Error restaurando stock del producto {product_id}: {e}')


@order_controller.route('/api/orders', methods=['GET'])
def get_all_orders():
    print('listado de ordenes')
    user_name = session.get('username')
    user_email = session.get('email')

    if not user_name or not user_email:
        return jsonify({'message': 'Información de usuario inválida'}), 401

    orders = Order.query.filter_by(user_name=user_name, user_email=user_email)\
                        .order_by(Order.id.desc()).all()
    result = [order.to_dict() for order in orders]
    return jsonify(result)


@order_controller.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    print('obteniendo orden')
    user_name = session.get('username')
    user_email = session.get('email')

    if not user_name or not user_email:
        return jsonify({'message': 'Información de usuario inválida'}), 401

    order = Order.query.filter_by(id=order_id, user_name=user_name, user_email=user_email).first()
    if not order:
        return jsonify({'message': 'Orden no encontrada'}), 404

    return jsonify(order.to_dict())


@order_controller.route('/api/orders', methods=['POST'])
def create_order():
    print('creando orden')
    data = request.get_json(silent=True)
    user_name = session.get('username')
    user_email = session.get('email')

    if not user_name or not user_email:
        return jsonify({'message': 'Información de usuario inválida'}), 401

    if not data:
        return jsonify({'message': 'Información de productos inválida'}), 400

    products = data.get('products')
    if not products or not isinstance(products, list):
        return jsonify({'message': 'Información de productos inválida'}), 400

    # Agrupar cantidades por producto (cantidad > 0)
    quantities = {}
    for item in products:
        if not isinstance(item, dict):
            return jsonify({'message': 'Información de productos inválida'}), 400
        product_id = item.get('product_id')
        quantity = item.get('quantity')
        try:
            product_id = int(product_id)
            quantity = int(quantity)
        except (TypeError, ValueError):
            return jsonify({'message': 'Información de productos inválida'}), 400
        if product_id <= 0 or quantity <= 0:
            return jsonify({'message': 'Información de productos inválida'}), 400
        quantities[product_id] = quantities.get(product_id, 0) + quantity

    base = products_service_url()
    if not base:
        return jsonify({'message': 'Servicio de productos no disponible'}), 500

    # 1. Consultar precio y existencias al servicio de Productos
    lines = []
    try:
        for product_id, quantity in quantities.items():
            response = requests.get(f'{base}/api/products/{product_id}', timeout=5)
            if response.status_code == 404:
                return jsonify({'message': f'Producto {product_id} no existe'}), 404
            if response.status_code != 200:
                return jsonify({'message': 'Error consultando el servicio de productos'}), 500
            product = response.json()
            lines.append({
                'product_id': product_id,
                'name': product.get('name'),
                'unit_price': Decimal(str(product['price'])),
                'available': int(product['quantity']),
                'quantity': quantity
            })
    except requests.exceptions.RequestException as e:
        print(f'Error consultando productos: {e}')
        return jsonify({'message': 'Servicio de productos no disponible'}), 500

    # 2. Verificar disponibilidad de inventario para TODAS las lineas antes de descontar
    for line in lines:
        if line['quantity'] > line['available']:
            return jsonify({'message': f'Inventario insuficiente para el producto {line["product_id"]}'}), 409

    # 3. Calcular el total de la venta
    total = Decimal('0')
    for line in lines:
        line['subtotal'] = line['unit_price'] * line['quantity']
        total += line['subtotal']

    # 4. Actualizar inventario en Productos (descontando la cantidad vendida)
    applied = []
    update_error = None
    try:
        for line in lines:
            response = requests.post(f'{base}/api/products/{line["product_id"]}/decrement',
                                     json={'quantity': line['quantity']}, timeout=5)
            if response.status_code == 409:
                update_error = (409, f'Inventario insuficiente para el producto {line["product_id"]}')
                break
            if response.status_code == 404:
                update_error = (404, f'Producto {line["product_id"]} no existe')
                break
            if response.status_code != 200:
                update_error = (500, 'Error actualizando el inventario en el servicio de productos')
                break
            applied.append((line['product_id'], line['quantity']))
    except requests.exceptions.RequestException as e:
        print(f'Error actualizando inventario: {e}')
        update_error = (500, 'Servicio de productos no disponible al actualizar inventario')

    if update_error:
        # Rollback: reponer el stock de las lineas ya descontadas. La orden NO se crea.
        restore_stock(applied)
        return jsonify({'message': update_error[1]}), update_error[0]

    # 5. Persistir la Order + order_items (solo si todo el inventario se actualizo)
    order = Order(user_name=user_name, user_email=user_email, total=total)
    for line in lines:
        order.items.append(OrderItem(
            product_id=line['product_id'],
            quantity=line['quantity'],
            unit_price=line['unit_price'],
            subtotal=line['subtotal']
        ))

    db.session.add(order)
    try:
        db.session.commit()
    except Exception as e:
        print(f'Error persistiendo la orden: {e}')
        db.session.rollback()
        restore_stock(applied)
        return jsonify({'message': 'Error interno al crear la orden'}), 500

    return jsonify({'message': 'Orden creada exitosamente',
                    'order_id': order.id,
                    'total': float(order.total)}), 201
