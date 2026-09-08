# microWebApp con Docker Compose (Parte 2)

Levanta todo el sistema (frontend, `microUsers`, `microProducts`, `microOrders` y un
MySQL independiente por microservicio) con un solo comando.

## Arquitectura

```
Navegador ──(solo :8080)──► frontend  (Flask + proxy /api/*)
                              │  ├──► microUsers   ──► users_db    (MySQL)
                              │  ├──► microProducts ──► products_db (MySQL)
                              │  └──► microOrders  ──► orders_db   (MySQL)
                              └──► microOrders ──► microProducts (HTTP, red interna)
```

* El navegador **solo** habla con el frontend (puerto `8080`). El frontend actúa como
  *API gateway*: reenvía `/api/users`, `/api/products`, `/api/orders` y `/api/login` al
  microservicio correspondiente usando las variables `USERS/PRODUCTS/ORDERS_SERVICE_URL`.
* Los microservicios **no exponen puertos** al host: se comunican por la red interna
  `app_network` usando el nombre del contenedor (`http://microorders:5004`, etc.).
* Cada microservicio tiene **su propia base de datos** MySQL con **volumen nombrado**
  (`users_db_data`, `products_db_data`, `orders_db_data`) para persistencia.

## Requisitos

* Docker Engine + Docker Compose v2 (`docker compose version`).

## Levantar el sistema

```bash
# 1) Crear el .env a partir del ejemplo (editar si se desea)
cp .env.example .env

# 2) Construir y levantar todo (las bases de datos se inicializan solas con los .sql)
docker compose up --build -d

# 3) Verificar que todo este arriba y las BD 'healthy'
docker compose ps

# 4) Ver los logs de un microservicio
docker compose logs -f microorders
```

## Probar el flujo completo (a traves del frontend :8080)

```bash
# Login (microUsers por proxy) -> guarda la cookie de sesion en cookies.txt
curl -s -c cookies.txt -X POST http://localhost:8080/api/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"juan","password":"123"}'

# Consultar catalogo (microProducts por proxy)
curl -s http://localhost:8080/api/products

# Consultar productos individuales (para armar la orden)
curl -s http://localhost:8080/api/products/1
curl -s http://localhost:8080/api/products/3

# Crear una orden (microOrders por proxy, usuario desde la sesion)
curl -s -b cookies.txt -X POST http://localhost:8080/api/orders \
  -H 'Content-Type: application/json' \
  -d '{"products":[{"product_id":1,"quantity":2},{"product_id":3,"quantity":1}]}'

# Listar y consultar las ordenes del usuario en sesion
curl -s -b cookies.txt http://localhost:8080/api/orders
curl -s -b cookies.txt http://localhost:8080/api/orders/1

# Casos de error esperados
curl -s -X POST http://localhost:8080/api/orders -H 'Content-Type: application/json' \
  -d '{"products":[{"product_id":1,"quantity":1}]}'                 # 401 sin sesion
curl -s -b cookies.txt http://localhost:8080/api/products/999       # 404 (via proxy)
```

### Desde la interfaz web

Abrir <http://localhost:8080>, iniciar sesión con `juan` / `123` (o `maria` / `456`) y
gestionar usuarios, productos y órdenes. Todas las llamadas JS usan rutas relativas
(`/api/...`) y pasan por el proxy del frontend.

## Persistencia de datos

Los datos viven en los volúmenes nombrados. Para comprobarlo:

```bash
docker compose restart          # o docker compose down && docker compose up -d
# los usuarios/productos/ordenes creados siguen existiendo
```

## Detener / limpiar

```bash
docker compose down             # detiene contenedores (conserva los volumenes)
docker compose down -v          # ademas borra los volumenes (BORRA los datos)
```

## Estructura de la infraestructura

```
.env.example            Variables globales (raiz) para docker compose
docker-compose.yml      Orquestacion: servicios + MySQLs + red + volumenes
Dockerfile              Uno por componente (frontend/, microUsers/, microProducts/, microOrders/)
microUsers/db/users_db.sql         Init de users_db (tabla users + juan/maria)
microProducts/db/products_db.sql   Init de products_db (3 productos de ejemplo)
microOrders/db/orders_db.sql       Init de orders_db (orders + order_items)
```

> Nota: En la Parte 3 se agregará Consul al `docker-compose.yml` y los microservicios
> (incluido el frontend) se registrarán con health checks; `microOrders` descubrirá a
> `microProducts` dinámicamente vía Consul en lugar de usar la URL fija.
