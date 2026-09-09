from flask import Blueprint, request, jsonify, session, g
from users.models.user_model import Users
from db.db import db
from datetime import timedelta
import os
import time
import threading
import atexit
import requests


user_controller = Blueprint('user_controller', __name__)

# Configuración de Consul
CONSUL_HOST = os.getenv('CONSUL_HOST', 'consul')
CONSUL_PORT = os.getenv('CONSUL_PORT', '8500')
SERVICE_NAME = os.getenv('SERVICE_NAME', 'users')
SERVICE_HOST = os.getenv('SERVICE_HOST', 'microusers')
SERVICE_PORT = int(os.getenv('SERVICE_PORT', '5002'))
SERVICE_ID = f"{SERVICE_NAME}-{SERVICE_PORT}"


@user_controller.route('/health', methods=['GET'])
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


@user_controller.route('/api/users', methods=['GET'])
def get_users():
    print("listado de usuarios")

    #print(g.__dict__)

    users = Users.query.all()
    result = [{'id':user.id, 'name': user.name, 'email': user.email, 'username': user.username} for user in users]
    return jsonify(result)

# Get single user by id
@user_controller.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    print("obteniendo usuario")
    user = Users.query.get_or_404(user_id)
    return jsonify({'id': user.id, 'name': user.name, 'email': user.email, 'username': user.username})

@user_controller.route('/api/users', methods=['POST'])
def create_user():
    print("creando usuario")
    data = request.json
    #new_user = Users(name="oscar", email="oscar@gmail", username="omondragon", password="123")
    new_user = Users(name=data['name'], email=data['email'], username=data['username'], password=data['password'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User created successfully'}), 201

# Update an existing user
@user_controller.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    print("actualizando usuario")
    user = Users.query.get_or_404(user_id)
    data = request.json
    user.name = data['name']
    user.email = data['email']
    user.username = data['username']
    # Solo se actualiza la contrasena si se envia un valor no vacio
    if data.get('password'):
        user.password = data['password']
    db.session.commit()
    return jsonify({'message': 'User updated successfully'})

# Delete an existing user
@user_controller.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = Users.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully'})

@user_controller.route('/api/login', methods=['POST'])
def login():
    data = request.json

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Missing username or password'}),400

    user = Users.query.filter_by(username=username).first()

    if not user:
        return jsonify({'message': 'Invalid username or password'}), 401

    #if not check_password_hash(user.password, password):
    if user.password != password:
        return jsonify({'message': 'Invalid username or password'}), 401

    # Store user information in session
    session['user_id'] = user.id
    session['username'] = user.username
    session['email'] = user.email  # Add other user information as needed

    #g.user=user

    #print(g.__dict__)
    print("En session: ",session)

    return jsonify({'message': 'Login successful'})


@user_controller.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logout successful'})
