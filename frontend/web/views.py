from flask import Flask, render_template, request, Response, jsonify, session, redirect
from flask_cors import CORS
from functools import wraps
import requests

app = Flask(__name__)
app.secret_key = 'secret123'
CORS(app, supports_credentials=True)
app.config.from_object('config.Config')


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('username') or not session.get('email'):
            return redirect('/')
        return view(*args, **kwargs)
    return wrapped


def resolve_service(api_path):
    # El frontend actua como puerta de entrada (API Gateway): reenvia /api/* al
    # microservicio correspondiente segun el prefijo de la ruta.
    if api_path.startswith('login') or api_path.startswith('logout') or api_path.startswith('users'):
        return app.config['USERS_SERVICE_URL'].rstrip('/')
    if api_path.startswith('products'):
        return app.config['PRODUCTS_SERVICE_URL'].rstrip('/')
    if api_path.startswith('orders'):
        return app.config['ORDERS_SERVICE_URL'].rstrip('/')
    return None


@app.route('/api/<path:api_path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_proxy(api_path):
    base = resolve_service(api_path)
    if not base:
        return jsonify({'message': 'Servicio no encontrado'}), 404

    url = f'{base}/api/{api_path}'

    headers = {}
    if request.headers.get('Cookie'):
        headers['Cookie'] = request.headers.get('Cookie')
    if request.mimetype:
        headers['Content-Type'] = request.mimetype

    try:
        upstream = requests.request(request.method, url,
                                    data=request.get_data(),
                                    headers=headers, timeout=60)
    except requests.exceptions.RequestException as e:
        print(f'Proxy error hacia {url}: {e}')
        return jsonify({'message': 'Microservicio no disponible'}), 502

    response = Response(upstream.content, status=upstream.status_code)
    if upstream.headers.get('Content-Type'):
        response.headers['Content-Type'] = upstream.headers['Content-Type']

    # Retransmitir las cookies de sesion que fijan los microservicios (login)
    for cookie in upstream.raw.headers.getlist('Set-Cookie'):
        response.headers.add('Set-Cookie', cookie)

    return response


# Ruta para renderizar el template index.html
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

# Ruta para renderizar el template users.html
@app.route('/users')
@login_required
def users():
    return render_template('users.html')

# Ruta para renderizar el template products.html
@app.route('/products')
@login_required
def products():
    return render_template('products.html')

# Ruta para renderizar el template orders.html
@app.route('/orders')
@login_required
def orders():
    return render_template('orders.html')

@app.route('/editUser/<string:id>')
@login_required
def edit_user(id):
    print("id recibido",id)
    return render_template('editUser.html', id=id)

@app.route('/editProduct/<string:id>')
@login_required
def edit_product(id):
    print("id recibido",id)
    return render_template('editProduct.html', id=id)

if __name__ == '__main__':
    app.run()
