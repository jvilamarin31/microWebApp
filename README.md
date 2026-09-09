# INTEGRANTES

1. Juan David Cuero Reina
2. Juan Esteban Vila Marin
3. Alejandro Rodriguez Cortes




-------
# microWebApp

Plataforma de e-commerce basada en **microservicios Flask** con persistencia desacoplada
(una base de datos MySQL por microservicio), frontend como puerta de entrada única
(API gateway con proxy inverso) y empaquetado reproducible con **Docker Compose**.

Proyecto académico de **Computación en la Nube** (especificación completa en `PROJECT_SPEC.md`).

## Features

- **Gestión de usuarios y autenticación:** CRUD de usuarios e inicio de sesión con sesión de Flask (cookie firmada).
- **Catálogo e inventario de productos:** CRUD y endpoints dedicados de stock (`decrement`/`increment`).
- **Órdenes de compra:** creación de órdenes multi-línea con validación de sesión, consulta de precios/existencias a `microProducts`, verificación de inventario **antes** de descontar, precio congelado al momento de la compra, rollback compensatorio ante fallos y consulta/listado de órdenes por usuario.
- **Persistencia desacoplada:** cada microservicio usa su propia base de datos (`users_db`, `products_db`, `orders_db`).
- **Frontend como API gateway:** el navegador solo habla con el frontend (rutas relativas `/api/...`); el frontend reenvía cada petición al microservicio correspondiente por variables de entorno (adiós a IPs/puertos hardcodeados).
- **Arranque reproducible:** todo el sistema levanta con un solo `docker compose up --build -d`.
- **Descubrimiento de servicios con Consul:** registro automático al iniciar, health checks en `/health`, descubrimiento dinámico de `microProducts` desde `microOrders` y resiliencia ante caídas (Parte 3).

## Stack

| Tecnología | Detalle |
|---|---|
| Python | 3.10 |
| Flask | 2.3.3 |
| Flask-SQLAlchemy / Flask-Cors | ORM y CORS |
| requests / python-dotenv | Proxy HTTP, llamadas a Consul y carga de `.env` |
| MySQL | 8.0 (una instancia/BD por microservicio) |
| HashiCorp Consul | 1.16 (Registro, health checks periódicos y descubrimiento dinámico) |
| Docker / Docker Compose | Empaquetado y orquestación |
| Vagrant (opcional) | VM Ubuntu 22.04 de desarrollo con Docker integrado |

## Estructura del proyecto

```
microWebApp/
├── frontend/                  # UI Flask + proxy /api/* + health check Consul (puerto 5001)
│   ├── web/                   # views.py (proxy y registro en Consul), templates/, static/
│   ├── Dockerfile
│   └── .dockerignore
├── microUsers/                # Gestión de usuarios y login (puerto 5002)
│   ├── users/                 # controllers/ (user_controller con Consul), models/, views.py
│   ├── db/users_db.sql        # Init de users_db (tabla users + juan/maria)
│   ├── config.py, run.py
│   ├── Dockerfile
│   └── .dockerignore
├── microProducts/             # Catálogo e inventario (puerto 5003)
│   ├── products/              # controllers/ (product_controller con Consul), models/, views.py
│   ├── db/products_db.sql     # Init de products_db (3 productos de ejemplo)
│   ├── config.py, run.py
│   ├── Dockerfile
│   └── .dockerignore
├── microOrders/               # Órdenes de compra y descubrimiento dinámico (puerto 5004)
│   ├── orders/                # controllers/ (order_controller con descubrimiento Consul), models/, views.py
│   ├── db/orders_db.sql       # Init de orders_db (orders + order_items)
│   ├── config.py, run.py
│   ├── Dockerfile
│   └── .dockerignore
├── docker-compose.yml         # Orquestación completa (Consul + frontend + 3 microservicios + 3 MySQL)
├── .env.example               # Variables globales para docker compose (raíz, incluye CONSUL_PORT)
├── Vagrantfile                # VM de desarrollo (con forwarded ports 8080 y 8500 y copia de compose)
├── script.sh                  # Provisionamiento de la VM (Docker + MySQL + preparación de .env)
└── PROJECT_SPEC.md            # Especificación del proyecto
```

## Requisitos previos

- **Opción Docker (recomendada):** solo [Docker](https://www.docker.com/) con Compose v2 (`docker compose version`).
- **Opción Vagrant:** [Vagrant](https://www.vagrantup.com/) + VirtualBox.
- **Opción local:** Python 3.10, MySQL 8 y `pip`.

## Configuración

### Variables globales (solo Docker)

Copia el archivo de ejemplo y completa los valores:

```bash
cp .env.example .env
```

| Variable | Descripción | Ejemplo |
|---|---|---|
| `MYSQL_ROOT_PASSWORD` | Contraseña del root de los tres contenedores MySQL | `root` |
| `DB_USER` | Usuario de aplicación creado en cada MySQL (con permisos solo sobre su BD) | `app` |
| `DB_PASSWORD` | Contraseña del usuario de aplicación | `app_password` |
| `SECRET_KEY` | Clave para firmar la sesión (debe ser la misma en frontend, microUsers y microOrders) | `secret123` |
| `FRONTEND_PORT` | Puerto publicado del frontend en el host | `8080` |

### Variables por microservicio (solo local/Vagrant)

Cada microservicio tiene su `.env.example` (`microUsers/`, `microProducts/`, `microOrders/`).
Sus `config.py` leen variables de entorno con valores por defecto que ya funcionan si tu MySQL
usa `root`/`root` en `localhost` y las tres BD `*_db` están creadas:

| Variable | Aplican a | Default |
|---|---|---|
| `MYSQL_HOST` | microUsers, microProducts, microOrders | `localhost` |
| `MYSQL_USER` / `MYSQL_PASSWORD` | microUsers, microProducts, microOrders | `root` / `root` |
| `MYSQL_DB` | microUsers / microProducts / microOrders | `users_db` / `products_db` / `orders_db` |
| `PRODUCTS_SERVICE_URL` | microOrders (servidor a servidor) | `http://localhost:5003` |
| `SECRET_KEY` | microUsers, microOrders, frontend | `secret123` |

El frontend también lee `USERS_SERVICE_URL`, `PRODUCTS_SERVICE_URL` y `ORDERS_SERVICE_URL`
(lado servidor, para el proxy). En Docker las inyecta `docker-compose.yml`
(`http://microusers:5002`, `http://microproducts:5003`, `http://microorders:5004`);
en local/VM usan `http://localhost:5002/5003/5004`.

## Cómo ejecutar

> En las tres opciones, el flujo de usuario es el mismo: el navegador abre el frontend y
> este reenvía `/api/...` al microservicio correspondiente.

### Opción Docker (recomendada)

Cada componente (`frontend`, `microUsers`, `microProducts`, `microOrders`) tiene su propio
`Dockerfile` (imagen `python:3.10-slim`, instalación de dependencias y `python run.py`).
El `docker-compose.yml` orquesta además un contenedor MySQL por microservicio con
volumen nombrado (`users_db_data`, `products_db_data`, `orders_db_data`) y healthcheck;
las bases de datos se inicializan automáticamente la primera vez con los scripts `db/*.sql`.
Solo el frontend publica puerto al host (`8080`); los microservicios se comunican por la red
interna `app_network` por nombre de contenedor.

```bash
# 1) Crear el .env a partir del ejemplo
cp .env.example .env

# 2) Construir y levantar todo
docker compose up --build -d

# 3) Verificar estado (las BD deben quedar 'healthy')
docker compose ps

# 4) Ver logs de un microservicio
docker compose logs -f microorders
```

La interfaz queda en <http://localhost:8080>.

### Opción Vagrant (VM)

`vagrant up` provisiona la VM: instala MySQL, crea y llena las tres bases de datos
(`users_db`, `products_db`, `orders_db`) con los scripts `db/*.sql` (mismo efecto que los
contenedores) e instala las dependencias de Python (incluidos `requests` y `python-dotenv`).

```bash
vagrant up
vagrant ssh servidorWeb
```

Dentro de la VM, corre cada aplicación en una terminal distinta:

```bash
cd /home/vagrant/microUsers    && python3 run.py   # puerto 5002
cd /home/vagrant/microProducts && python3 run.py   # puerto 5003
cd /home/vagrant/microOrders   && python3 run.py   # puerto 5004
cd /home/vagrant/frontend      && python3 run.py   # puerto 5001
```

Desde el host abre <http://192.168.56.3:5001> (IP definida en el `Vagrantfile`). El proxy del
frontend dentro de la VM usa `localhost` para llegar a los microservicios, así que no hay que
configurar IPs adicionales.

### Opción local

Requisitos: Python 3.10, MySQL 8 corriendo y `pip`.

1. Crea las bases de datos (usuarios/productos con datos de ejemplo):

```bash
mysql -u root -p < microUsers/db/users_db.sql
mysql -u root -p < microProducts/db/products_db.sql
mysql -u root -p < microOrders/db/orders_db.sql
```

2. Crea un entorno virtual e instala las dependencias:

```bash
python3 -m venv venv && source venv/bin/activate
pip install Flask==2.3.3 Flask-Cors==4.0.0 Flask-SQLAlchemy==3.1.1 mysqlclient PyMySQL requests python-dotenv
```

> El código usa URI `mysql://...`, por lo que requiere `mysqlclient`. En Debian/Ubuntu
> instala antes: `sudo apt install default-libmysqlclient-dev build-essential pkg-config python3-dev`.

3. Correr cada microservicio (y el frontend) desde su carpeta, en terminales distintas:

```bash
cd microUsers    && python run.py   # puerto 5002
cd microProducts && python run.py   # puerto 5003
cd microOrders   && python run.py   # puerto 5004
cd frontend      && python run.py   # puerto 5001
```

Abre <http://localhost:5001>. Si tu MySQL no usa `root`/`root`, copia el `.env.example`
correspondiente a `.env` en cada microservicio y ajusta las credenciales.

## Endpoints

> En todos los entornos el navegador los consume **a través del frontend** con rutas
> relativas (`/api/...`). Los listados a continuación corresponden a la API de cada
> microservicio (vía proxy en el puerto del frontend, o directa en su puerto interno).

### microUsers — `/api/...`

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/login` | Inicio de sesión (crea la cookie de sesión) |
| `GET` | `/api/users` | Listar usuarios |
| `GET` | `/api/users/{id}` | Ver detalle de un usuario |
| `POST` | `/api/users` | Crear usuario |
| `PUT` | `/api/users/{id}` | Actualizar usuario |
| `DELETE` | `/api/users/{id}` | Eliminar usuario |

### microProducts — `/api/...`

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/products` | Listar productos |
| `GET` | `/api/products/{id}` | Ver producto (precio y existencias) |
| `POST` | `/api/products` | Crear producto |
| `PUT` | `/api/products/{id}` | Actualizar producto |
| `DELETE` | `/api/products/{id}` | Eliminar producto |
| `POST` | `/api/products/{id}/decrement` | Descontar stock (lo usa microOrders al crear una orden) |
| `POST` | `/api/products/{id}/increment` | Reponer stock (lo usa microOrders para rollback) |

### microOrders — `/api/...` (requiere sesión)

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/orders` | Listar órdenes del usuario en sesión |
| `GET` | `/api/orders/{id}` | Ver una orden con sus ítems |
| `POST` | `/api/orders` | Crear una orden |

Códigos de error: `400` (petición mal formada), `401` (sin sesión), `404` (no existe),
`409` (inventario insuficiente), `500` (error interno, p. ej. microProducts no disponible).

Ejemplo de creación de orden:

```json
{
  "products": [
    { "product_id": 1, "quantity": 2 },
    { "product_id": 3, "quantity": 1 }
  ]
}
```

## Prueba rápida (Docker)

Usuarios de ejemplo: `juan` / `123` y `maria` / `456`.

```bash
# Login (guarda la cookie en cookies.txt)
curl -s -c cookies.txt -X POST http://localhost:8080/api/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"juan","password":"123"}'

# Catálogo
curl -s http://localhost:8080/api/products

# Crear una orden (2 laptops + 1 teclado)
curl -s -b cookies.txt -X POST http://localhost:8080/api/orders \
  -H 'Content-Type: application/json' \
  -d '{"products":[{"product_id":1,"quantity":2},{"product_id":3,"quantity":1}]}'

# Listar y consultar las órdenes del usuario
curl -s -b cookies.txt http://localhost:8080/api/orders
curl -s -b cookies.txt http://localhost:8080/api/orders/1

# Casos de error
curl -s -X POST http://localhost:8080/api/orders -H 'Content-Type: application/json' \
  -d '{"products":[{"product_id":1,"quantity":1}]}'                  # 401 sin sesión
curl -s -b cookies.txt http://localhost:8080/api/products/999        # 404
curl -s -b cookies.txt -X POST http://localhost:8080/api/orders \
  -H 'Content-Type: application/json' \
  -d '{"products":[{"product_id":1,"quantity":999}]}'                # 409 stock insuficiente
```

Productos semilla: Laptop (3500.00, 10 uds), Mouse (25.50, 50 uds), Teclado (120.00, 30 uds).

## Persistencia (Docker)

Los datos viven en volúmenes nombrados y sobreviven al reinicio:

```bash
docker compose restart          # o docker compose down && docker compose up -d
docker compose down             # detiene contenedores (conserva los volúmenes)
docker compose down -v          # además borra los volúmenes (BORRA los datos)
```

## Descubrimiento de Servicios con Consul (Parte 3)

Consul corre como servicio orquestado en `docker-compose` en el puerto `8500` (`agent -dev -client=0.0.0.0`).
La lógica de registro, health check y descubrimiento se implementó **directamente dentro del controller de cada microservicio**, siguiendo las prácticas trabajadas en clase.

### 1. Arquitectura de Registro y Health Checks

Cada componente expone un endpoint HTTP de salud y ejecuta un hilo en segundo plano que lo registra ante la API de Consul (`PUT /v1/agent/service/register`):

| Componente | Archivo donde se implementó | Servicio en Consul | Puerto Interno | Endpoint de Salud |
|---|---|---|---|---|
| `microUsers` | `microUsers/users/controllers/user_controller.py` | `users` | `5002` | `GET /health` |
| `microProducts` | `microProducts/products/controllers/product_controller.py` | `products` | `5003` | `GET /health` |
| `microOrders` | `microOrders/orders/controllers/order_controller.py` | `orders` | `5004` | `GET /health` |
| `frontend` | `frontend/web/views.py` | `frontend` | `5001` | `GET /health` |

**Características del mecanismo de registro:**
- **Chequeo periódico:** Consul sondea cada `10s` (timeout de `3s`) el endpoint `/health` de cada contenedor.
- **Persistencia en estado crítico (24 horas):** Se configuró `"DeregisterCriticalServiceAfter": "24h"`. Esto asegura que si un servicio se apaga, Consul **NO lo borra del catálogo**, sino que lo mantiene visible en la UI con la **X roja (Critical/Failing)** para la demostración de la sustentación.
- **Auto-registro continuo en bucle:** Cada servicio mantiene un hilo en segundo plano (`daemon=True`) que cada 20 segundos verifica y renueva su registro ante Consul. Si Consul se reinicia o se vacía la memoria, los microservicios se re-registran automáticamente sin intervención manual.

### 2. Descubrimiento Dinámico de Servicios (`microOrders -> microProducts`)

En `microOrders/orders/controllers/order_controller.py`, la función `products_service_url()` ya **no depende de una URL estática ni de variables de entorno quemadas**. En su lugar, consulta la API en vivo de Consul:

```python
consul_url = f"http://{CONSUL_HOST}:{CONSUL_PORT}/v1/health/service/products?passing"
resp = requests.get(consul_url, timeout=3)
```

1. Consul devuelve la lista de instancias saludables del servicio `products`.
2. `order_controller.py` extrae dinámicamente la dirección del host (`microproducts`) y su puerto (`5003`).
3. Emite un log explícito en consola para la sustentación:
   ```text
   [Consul Discovery] Servicio 'products' descubierto en http://microproducts:5003
   ```
4. Si la instancia de productos está caída o no saludable, Consul devuelve lista vacía y `microOrders` responde controladamente con código HTTP `500` (*"Servicio de productos no disponible"*), evitando inconsistencias en base de datos.

### 3. Monitoreo y UI de Consul

Abre en tu navegador la consola web de Consul:
👉 <http://localhost:8500/ui> (o a través de la IP de la VM: <http://192.168.56.3:8500/ui>)

Verás los **4 servicios** (`frontend`, `orders`, `products`, `users`) con sus health checks en verde (**passing**).

Para consultar el estado desde la terminal (como indica el PDF del profesor):

```bash
# Consultar catálogo de servicios registrados
curl -s http://localhost:8500/v1/catalog/services

# Consultar instancias saludables del servicio de productos
curl -s http://localhost:8500/v1/health/service/products?passing | jq '.[].Service'
```

### 4. Prueba de Resiliencia (Paso a paso para la Sustentación)

Esta es la prueba clave que evaluará el docente (0.2 pts de la rúbrica):

1. **Monitorear los logs de órdenes:**
   En una terminal, pon a correr:
   ```bash
   docker compose logs -f microorders
   ```
2. **Crear una orden con el sistema normal:**
   Inicia sesión en <http://localhost:8080> y haz un pedido. Verás en los logs:
   ```text
   [Consul Discovery] Servicio 'products' descubierto en http://microproducts:5003
   ```
3. **Simular caída de productos:**
   ```bash
   docker compose stop microproducts
   ```
4. **Verificar en Consul:**
   Abre <http://localhost:8500/ui>. En 10 segundos, el servicio `products` pasará a estado crítico con la **X roja**.
5. **Comprobar fallo controlado:**
   Intenta crear una nueva orden. La API responderá con `500 Servicio de productos no disponible` y la orden NO se creará en base de datos.
6. **Recuperación del servicio:**
   ```bash
   docker compose start microproducts
   ```
7. **Redescubrimiento automático:**
   En 10 segundos, Consul verifica `/health`, vuelve a poner a `products` en **verde (passing)**, y `microOrders` lo redescubre inmediatamente. Las compras vuelven a procesarse sin reiniciar ningún otro contenedor.

## Documentación

- `PROJECT_SPEC.md` — especificación y rúbrica del microproyecto (Partes 1-3).

## Licencia

[MIT](LICENSE)
