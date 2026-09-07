from flask import Blueprint, request, jsonify, session, current_app
from db.db import db
from orders.models.order_model import Order, OrderItem
from decimal import Decimal
import requests


order_controller = Blueprint('order_controller', __name__)


def products_service_url():
    return current_app.config['PRODUCTS_SERVICE_URL'].rstrip('/')


def restore_stock(applied):
    base = products_service_url()
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
