from flask import Blueprint, request, jsonify
from db.db import db
from products.models.product_model import Products


product_controller = Blueprint('product_controller', __name__)


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
