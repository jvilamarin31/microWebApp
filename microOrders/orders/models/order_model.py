from db.db import db


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(100), nullable=False)
    user_email = db.Column(db.String(100), nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    status = db.Column(db.String(20), nullable=False, default='created')
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    items = db.relationship('OrderItem', cascade='all, delete-orphan', backref='order', lazy=True)

    def __init__(self, user_name, user_email, total, status='created'):
        self.user_name = user_name
        self.user_email = user_email
        self.total = total
        self.status = status

    def to_dict(self):
        return {
            'id': self.id,
            'user_name': self.user_name,
            'user_email': self.user_email,
            'total': float(self.total),
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'items': [item.to_dict() for item in self.items]
        }


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)

    def __init__(self, product_id, quantity, unit_price, subtotal):
        self.product_id = product_id
        self.quantity = quantity
        self.unit_price = unit_price
        self.subtotal = subtotal

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price),
            'subtotal': float(self.subtotal)
        }
