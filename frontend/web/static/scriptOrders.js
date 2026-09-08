function loadOrders() {
    const container = document.getElementById('orders-list');
    container.innerHTML = '<div class="alert alert-info">Cargando órdenes...</div>';

    fetch('/api/orders', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        },
        credentials: 'include'
    })
    .then(response => response.json().then(data => ({ status: response.status, data })))
    .then(({ status, data }) => {
        if (status === 401) {
            container.innerHTML = '<div class="alert alert-warning">Debes iniciar sesión para ver tus órdenes.</div>';
            return;
        }
        if (!Array.isArray(data)) {
            container.innerHTML = '<div class="alert alert-danger">' +
                ((data && data.message) || 'No se pudieron cargar las órdenes.') + '</div>';
            return;
        }
        renderOrders(data, container);
    })
    .catch(error => {
        console.error('Error:', error);
        container.innerHTML = '<div class="alert alert-danger">Ocurrió un error al cargar las órdenes.</div>';
    });
}

function renderOrders(orders, container) {
    if (orders.length === 0) {
        container.innerHTML = '<div class="alert alert-info">Aún no tienes órdenes.</div>';
        return;
    }

    const html = orders.map(order => {
        const items = (order.items || []).map(item =>
            `<tr>
                <td>#${item.product_id}</td>
                <td>${item.quantity}</td>
                <td>$${Number(item.unit_price).toFixed(2)}</td>
                <td>$${Number(item.subtotal).toFixed(2)}</td>
            </tr>`
        ).join('');

        return `
        <div class="card mb-3">
            <div class="card-header">
                <strong>Orden #${order.id}</strong> — ${order.created_at || ''} —
                <span class="badge badge-secondary">${order.status}</span>
                <span class="float-right">Total: <strong>$${Number(order.total).toFixed(2)}</strong></span>
            </div>
            <div class="card-body p-0">
                <table class="table table-sm table-striped mb-0">
                    <thead>
                        <tr>
                            <th>Producto</th>
                            <th>Cantidad</th>
                            <th>Precio unit.</th>
                            <th>Subtotal</th>
                        </tr>
                    </thead>
                    <tbody>${items}</tbody>
                </table>
            </div>
        </div>`;
    }).join('');

    container.innerHTML = html;
}
