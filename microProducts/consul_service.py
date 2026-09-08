import os
import time
import threading
import atexit
import requests
from flask import jsonify

def get_consul_url():
    host = os.getenv('CONSUL_HOST', 'consul')
    port = os.getenv('CONSUL_PORT', '8500')
    return f"http://{host}:{port}"

def get_service_config(service_name_default='products', service_port_default=5003, service_host_default='microproducts'):
    service_name = os.getenv('SERVICE_NAME', service_name_default)
    service_port = int(os.getenv('SERVICE_PORT', service_port_default))
    service_host = os.getenv('SERVICE_HOST', service_host_default)
    service_id = os.getenv('SERVICE_ID', f"{service_name}-{service_port}")
    return service_name, service_host, service_port, service_id

def deregister_service(service_id=None):
    if not service_id:
        _, _, _, service_id = get_service_config()
    consul_url = get_consul_url()
    try:
        url = f"{consul_url}/v1/agent/service/deregister/{service_id}"
        resp = requests.put(url, timeout=3)
        if resp.status_code == 200:
            print(f"[Consul] Servicio '{service_id}' desregistrado exitosamente.")
    except Exception as e:
        print(f"[Consul] Advertencia: No se pudo desregistrar '{service_id}': {e}")

def register_service(app, service_name_default='products', service_port_default=5003, service_host_default='microproducts'):
    service_name, service_host, service_port, service_id = get_service_config(
        service_name_default, service_port_default, service_host_default
    )

    # Registrar endpoint /health si aun no esta presente
    if not any(rule.rule == '/health' for rule in app.url_map.iter_rules()):
        @app.route('/health', methods=['GET'])
        def health_check():
            return jsonify({
                "status": "healthy",
                "service": service_name,
                "host": service_host,
                "port": service_port
            }), 200

    def _register_worker():
        consul_url = get_consul_url()
        # Esperar a que el servidor Flask local responda
        local_url = f"http://127.0.0.1:{service_port}/health"
        for _ in range(20):
            try:
                r = requests.get(local_url, timeout=1)
                if r.status_code == 200:
                    break
            except Exception:
                pass
            time.sleep(1)

        payload = {
            "ID": service_id,
            "Name": service_name,
            "Address": service_host,
            "Port": service_port,
            "Check": {
                "HTTP": f"http://{service_host}:{service_port}/health",
                "Interval": "10s",
                "Timeout": "3s",
                "DeregisterCriticalServiceAfter": "1m"
            }
        }

        url = f"{consul_url}/v1/agent/service/register"
        for attempt in range(1, 15):
            try:
                res = requests.put(url, json=payload, timeout=3)
                if res.status_code == 200:
                    print(f"[Consul] Servicio '{service_name}' ({service_id}) registrado exitosamente en Consul ({service_host}:{service_port})")
                    break
                else:
                    print(f"[Consul] Intento {attempt}: Respuesta de registro {res.status_code}: {res.text}")
            except Exception as e:
                print(f"[Consul] Intento {attempt}: Consul aun no disponible en {consul_url} ({e})")
            time.sleep(2)

    thread = threading.Thread(target=_register_worker, daemon=True)
    thread.start()
    atexit.register(deregister_service, service_id)
