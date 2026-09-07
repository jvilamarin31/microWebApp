# MICRO PROYECTO 1 COMPUTACIÓN EN LA NUBE

**Universidad Autónoma de Occidente**
**Facultad de Ingeniería**
**Programa:** Ing. Informática / Ing. de Datos e IA / Ing. Multimedia / Ing. Electrónica y Tel.
**Asignatura:** Computación en la Nube
**Sustentación:** Septiembre 9 de 2026
**Valoración:** 5.0 pts
**Docente:** Oscar H. Mondragón, Ph.D.
**Código Base:** https://github.com/omondragon/microWebAppParcial

---

## Contexto y Objetivo

El propósito de este microproyecto es completar un sitio de administración de usuarios, productos y órdenes de compra, añadiendo la funcionalidad faltante para la gestión de órdenes. Se entrega una estructura de frontend y la implementación del microservicio de usuarios, que puede usar como referencia o reimplementar.

Su tarea consiste en integrar el microservicio de productos (implementado en las prácticas del curso) y diseñar, implementar e integrar el microservicio de órdenes de compra, con persistencia desacoplada, empaquetado en contenedores y descubrimiento dinámico de servicios.

---

## Arquitectura Objetivo

* **Orquestación:** docker-compose (red interna + volúmenes persistentes)
* **Descubrimiento y Registro:** Consul (Registro, Health Checks, Descubrimiento)
* **Frontend:** Gestión de interfaz y usuario
* **microUsers:** Gestión de usuarios (login) -> Base de datos MySQL `users_db`
* **microProducts:** Catálogo e inventario -> Base de datos MySQL `products_db`
* **microOrders:** Órdenes de compra a implementar -> Base de datos MySQL `orders_db` (Se comunica vía HTTP con `microProducts`)

**Flujo de comunicación:**
* Frontend -> microUsers (login / sesión)
* Frontend -> microProducts (catálogo)
* Frontend -> microOrders (creación de órdenes)
* microOrders -> microProducts (vía HTTP / API, usando Consul para descubrir URL)

---

## Instrucciones Generales y Entregables

* **Modalidad:** Trabajo en grupo (grupos ya conformados). Todos los integrantes deben poder explicar y ejecutar cualquier parte durante la sustentación.
* **Entregable en GitHub:** Un repositorio con todo el código de los microservicios, los Dockerfile, el `docker-compose.yml`, los scripts de inicialización de las bases de datos y un `.env` de ejemplo.
* **Reproducibilidad:** El sistema completo debe levantarse con un único `docker-compose up` desde el repositorio, sin pasos manuales adicionales.
* **Sustentación y evidencia en vivo:** La evaluación es una demostración en tiempo real. El docente podrá pedir a cualquier integrante levantar el entorno, invocar endpoints y provocar fallos para observar el comportamiento.
* **Integridad académica:** El uso de asistentes de IA debe declararse y el grupo debe poder explicar cada componente entregado.

---

## PRIMERA PARTE: Microservicio de Órdenes con Persistencia Desacoplada (2.0 pts)

### Persistencia desacoplada
1. **Cada microservicio con su propia base de datos:** Levante un contenedor MySQL independiente por microservicio (`users_db`, `products_db`, `orders_db`) en `docker-compose`. Ningún microservicio accede directamente a la base de datos de otro; la comunicación entre servicios es siempre vía su API HTTP.
2. **Credenciales por entorno:** Las cadenas de conexión y contraseñas se pasan por variables de entorno (`.env`), nunca hardcodeadas en el código.
3. **Datos persistentes:** Cada MySQL usa un volumen nombrado para que los datos sobrevivan al reinicio de los contenedores.

### Microservicio de productos
4. Integre el microservicio de productos implementado en las prácticas del curso. Debe exponer, como mínimo, la consulta de un producto por ID y la actualización de su inventario (necesaria para el flujo de órdenes).

### Microservicio de órdenes
5. Implemente el microservicio de órdenes siguiendo una estructura como la sugerida, integrándola al código suministrado:

```text
microOrders/
├── config.py
├── db/
│   └── db.py
├── orders/
│   ├── controllers/
│   │   └── order_controller.py
│   ├── models/
│   │   └── order_model.py
│   └── views.py
└── run.py
```

#### Modelo de datos
Una orden agrupa varios productos con sus cantidades, por lo que se requieren al menos dos entidades relacionadas:
* `orders`: `id`, `user_name`, `user_email`, `total`, `status`, `created_at`.
* `order_items`: `id`, `order_id` (FK → `orders`), `product_id`, `quantity`, `unit_price`, `subtotal`.

*Nota:* Guarde el precio unitario y el subtotal en `order_items` al momento de la compra: el precio del producto puede cambiar después, y la orden debe conservar el valor con el que se vendió.

#### Contrato de la API (endpoints a implementar)
* `GET /api/orders` - Lista las órdenes del usuario en sesión.
* `GET /api/orders/<id>` - Devuelve una orden con sus ítems.
* `POST /api/orders` - Crea una orden. Ejemplo de cuerpo de la petición:
```json
{
  "products": [
    { "product_id": 3, "quantity": 2 },
    { "product_id": 7, "quantity": 1 }
  ]
}
```

#### Lógica esperada de `POST /api/orders` (tomando el usuario desde la sesión):
a. Validar que exista sesión de usuario y que la lista de productos sea válida (cantidades > 0).
b. Para cada producto, consultar al microservicio de productos su precio y existencias.
c. Verificar disponibilidad de inventario para todas las líneas antes de confirmar.
d. Calcular el total de la venta.
e. Actualizar el inventario invocando el endpoint de actualización del microservicio de productos.
f. Crear la orden y sus ítems y persistirlos en `orders_db`.

#### Esqueleto sugerido para `order_controller.py`:
```python
@order_controller.route('/api/orders', methods=['GET'])
def get_all_orders():
    # INSERTAR SU CODIGO AQUI
    pass

@order_controller.route('/api/orders/', methods=['GET'])
def get_order(order_id):
    # INSERTAR SU CODIGO AQUI
    pass

@order_controller.route('/api/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    user_name = session.get('username')
    user_email = session.get('email')

    if not user_name or not user_email:
        return jsonify({'message': 'Información de usuario inválida'}), 401

    products = data.get('products')
    if not products or not isinstance(products, list):
        return jsonify({'message': 'Información de productos inválida'}), 400

    # 1. Consultar precios/existencias al servicio de Productos
    # 2. Verificar disponibilidad de inventario
    # 3. Calcular el total de la venta
    # 4. Actualizar inventario (endpoint de Productos)
    # 5. Crear la Order + order_items y guardarlas en la BD
    return jsonify({'message': 'Orden creada exitosamente'}), 201
```

#### Manejo de errores
Devuelva códigos HTTP coherentes con la causa del error:
* **400:** Petición mal formada (falta información o formato inválido).
* **401:** No hay sesión de usuario válida.
* **404:** Producto no existe.
* **409:** Inventario insuficiente para alguna línea de la orden.
* **500:** Error interno (incluida la indisponibilidad del servicio de productos).

*Nota:* Considere la consistencia ante fallos: si la actualización de inventario falla a mitad de un pedido con varias líneas, la orden no debe quedar registrada como confirmada. Verifique la disponibilidad de todas las líneas antes de descontar inventario y describa en la sustentación cómo evita órdenes inconsistentes.

#### Entregables Parte 1
* **En GitHub:** Microservicio de órdenes completo (modelos, controladores, vistas) e integración del de productos.
* **Scripts de creación de las bases de datos:** (`orders_db` con `orders` y `order_items`).
* **En la sustentación:** Creación de una orden válida, listado y consulta, y los casos de error 401/404/409.

#### Rúbrica Parte 1 (2.0 pts)
* Persistencia desacoplada: una BD MySQL por microservicio (0.3)
* Modelo de datos correcto (`orders` + `order_items`) y persistencia (0.3)
* Endpoints GET (listar y consultar) funcionando (0.3)
* `POST /api/orders`: cálculo de total y creación de la orden (0.4)
* Llamada al servicio de productos: verificación y actualización de inventario (0.4)
* Manejo de errores con códigos HTTP correctos (0.3)
* **Total:** 2.0 pts

---

## SEGUNDA PARTE: Empaquetado de la aplicación con Docker y Docker Compose (2.0 pts)

### Requerimientos
1. **Dockerfile por microservicio:** Cree un `Dockerfile` para cada microservicio (usuarios, productos, órdenes) y para el frontend, con una imagen base adecuada, instalación de dependencias y comando de arranque.
2. **Orquestación con docker-compose:** Un `docker-compose.yml` debe levantar todos los servicios y sus bases de datos. Debe incluir:
   * Servicios para frontend, `microUsers`, `microProducts`, `microOrders` y un contenedor MySQL por microservicio.
   * Volúmenes nombrados para cada MySQL (persistencia de datos).
   * Red interna para que los servicios se comuniquen por nombre de servicio.
   * Variables de entorno (vía `.env`) para credenciales y parámetros de conexión.
   * `depends_on` con `healthcheck` para que cada microservicio arranque solo cuando su base de datos esté lista.
   * Puertos expuestos solo donde sea necesario (p. ej. frontend).
3. **Arranque reproducible:** Todo el sistema debe quedar operativo con un solo comando, sin pasos manuales.
   ```bash
   docker compose up --build -d
   docker compose ps
   # todos los servicios 'healthy'
   docker compose logs -f microOrders
   ```

### Verificación
4. Demuestre que los contenedores levantan correctamente y quedan en estado saludable.
5. Ejecute el flujo completo (login, consulta de productos, creación de una orden) contra el sistema en contenedores.
6. Persistencia: reinicie los contenedores (`docker compose restart` o `down`/`up` sin borrar volúmenes) y demuestre que los datos (usuarios, productos, órdenes) se conservan.

Ejemplo de prueba de un endpoint dentro del sistema contenedorizado:
```bash
curl -s -X POST http://localhost:8080/api/orders \
  -H 'Content-Type: application/json' --cookie 'session=...' \
  -d '{"products":[{"product_id": 3, "quantity":2}]}'
```

#### Entregables Parte 2
* **En GitHub:** `Dockerfile` de cada componente, `docker-compose.yml` y `.env` de ejemplo.
* **En la sustentación:** `docker compose up` desde cero, estado saludable de los servicios y flujo funcional.
* **Demostración de persistencia de datos** tras reinicio de contenedores.

#### Rúbrica Parte 2 (2.0 pts)
* Dockerfile correcto por microservicio y frontend (0.5)
* `docker-compose` orquesta todos los servicios + una BD por microservicio (0.5)
* Volúmenes (persistencia) y red interna configurados (0.4)
* Variables de entorno / `.env` (sin credenciales hardcodeadas) (0.2)
* Sistema operativo con un solo `docker compose up` y flujo funcional (0.4)
* **Total:** 2.0 pts

---

## TERCERA PARTE: Descubrimiento de servicios con Consul (1.0 pt)

### Requerimientos
1. **Consul en el compose:** Agregue Consul como un servicio más del `docker-compose`.
2. **Registro automático:** Cada microservicio debe registrarse en Consul al iniciar (nombre del servicio, dirección y puerto).
3. **Health checks:** Cada microservicio expone un endpoint de salud (p. ej. `/health`) y registra en Consul un health check que Consul consulta periódicamente.
4. **Descubrimiento dinámico:** El microservicio de órdenes NO debe tener hardcodeada la URL del servicio de productos. Debe consultar a Consul para descubrir dinámicamente la dirección IP y el puerto del servicio de productos antes de invocarlo.
5. **Baja al terminar (deseable):** Los servicios se de-registran de Consul al detenerse.

### Verificación
6. **UI de Consul:** Muestre en la interfaz de Consul (puerto 8500) todos los servicios registrados y en estado saludable.
7. **Descubrimiento en acción:** Cree una orden y evidencie (por logs) que órdenes resolvió la dirección de productos vía Consul, sin URL fija.
8. **Resiliencia:** Detenga la instancia de productos y muestre que Consul la marca como no saludable; vuelva a levantarla y muestre que órdenes la redescubre y opera de nuevo.

Ejemplo de consulta a la API de Consul:
```bash
curl -s http://localhost:8500/v1/health/service/products?passing | jq '.[].Service'
```

#### Entregables Parte 3
* **En GitHub:** Código de registro/health check y de descubrimiento vía Consul, y el servicio Consul en el compose.
* **En la sustentación:** UI de Consul con servicios saludables, orden creada con descubrimiento dinámico y prueba de resiliencia.

#### Rúbrica Parte 3 (1.0 pt)
* Consul en el compose y microservicios registrados al iniciar (0.3)
* Health checks funcionando (servicios saludables en Consul) (0.2)
* Órdenes descubre productos vía Consul (sin URL hardcodeada) (0.3)
* Prueba de resiliencia (caída y redescubrimiento del servicio) (0.2)
* **Total:** 1.0 pt

---

## Consolidado de Evaluación
* Parte 1: Microservicio de órdenes con persistencia desacoplada (2.0 pts)
* Parte 2: Empaquetado con Docker y Docker Compose (2.0 pts)
* Parte 3: Descubrimiento de servicios con Consul (1.0 pt)
* **TOTAL:** 5.0 pts

