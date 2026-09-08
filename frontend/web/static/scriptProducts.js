function getProducts() {
    fetch('/api/products', {
     method: 'GET',
     headers: {
        'Content-Type': 'application/json'
        },
     credentials: 'include'
    })
        .then(response => response.json())
        .then(data => {
            // Handle data
            console.log(data);

            // Get table body
            var productListBody = document.querySelector('#product-list tbody');
            productListBody.innerHTML = ''; // Clear previous data

            // Loop through products and populate table rows
            data.forEach(product => {
                var row = document.createElement('tr');

                // Id
                var idCell = document.createElement('td');
                idCell.textContent = product.id;
                row.appendChild(idCell);

                // Name
                var nameCell = document.createElement('td');
                nameCell.textContent = product.name;
                row.appendChild(nameCell);

                // Price
                var priceCell = document.createElement('td');
                priceCell.textContent = product.price;
                row.appendChild(priceCell);

                // Quantity
                var quantityCell = document.createElement('td');
                quantityCell.textContent = product.quantity;
                row.appendChild(quantityCell);

		// Order
		var orderInput = document.createElement('input');
		orderInput.type = 'text';
		orderInput.value = "0";
		row.appendChild(orderInput);

                // Actions
                var actionsCell = document.createElement('td');

                // Edit link
                var editLink = document.createElement('a');
                editLink.href = `/editProduct/${product.id}`;
                //editLink.href = `edit.html?id=${product.id}`;
                editLink.textContent = 'Edit';
                editLink.className = 'btn btn-primary mr-2';
                actionsCell.appendChild(editLink);

                // Delete link
                var deleteLink = document.createElement('a');
                deleteLink.href = '#';
                deleteLink.textContent = 'Delete';
                deleteLink.className = 'btn btn-danger';
                deleteLink.addEventListener('click', function() {
                    deleteProduct(product.id);
                });
                actionsCell.appendChild(deleteLink);

                row.appendChild(actionsCell);

                productListBody.appendChild(row);
            });
        })
        .catch(error => console.error('Error:', error));
}

function createProduct() {
    var data = {
        name: document.getElementById('name').value,
        price: document.getElementById('price').value,
        quantity: document.getElementById('quantity').value
    };

    fetch('/api/products', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        // Handle success
        console.log(data);
    })
    .catch(error => {
        // Handle error
        console.error('Error:', error);
    });
}

function updateProduct() {

    //const userName = '{{ username }}';
    //console.log('userName: ',userName);

    var productId = document.getElementById('product-id').value;
    var data = {
        name: document.getElementById('name').value,
        price: document.getElementById('price').value,
        quantity: document.getElementById('quantity').value
    };

    fetch(`/api/products/${productId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        // Handle success
        console.log('Product updated successfully:', data);
        // Redirigir al listado tras guardar los cambios
        window.location.href = '/products';
    })
    .catch(error => {
        // Handle error
        console.error('Error:', error);
        alert('No se pudo actualizar el producto. Intenta nuevamente.');
    });
}



function deleteProduct(productId) {
    console.log('Deleting product with ID:', productId);
    if (confirm('Are you sure you want to delete this product?')) {
        fetch(`/api/products/${productId}`, {
            method: 'DELETE',
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Handle success
            console.log('Product deleted successfully:', data);
            // Reload the product list
            getProducts();
        })
        .catch(error => {
            // Handle error
            console.error('Error:', error);
        });
    }
}


function orderProducts() {
  // Obtener los productos seleccionados y sus cantidades
  const selectedProducts = [];
  const productRows = document.querySelectorAll('#product-list tbody tr');
  productRows.forEach(row => {
    const quantityInput = row.querySelector('input[type="text"]');
    const quantity = parseInt(quantityInput.value);
    if (quantity > 0) {
      //const productId = row.id.split('-')[1]; // Extraer el ID del producto del atributo id de la fila
	    //
      var productId = row.querySelector('td:nth-child(1)').textContent;
      //const productId = row.id.textContent; // Extraer el ID del producto del atributo id de la fila
      selectedProducts.push({ product_id: parseInt(productId, 10), quantity });
    }
  });

  // Si no hay productos seleccionados, mostrar un mensaje de error
  if (selectedProducts.length === 0) {
    alert('Por favor, selecciona al menos un producto para realizar la orden.');
    return;
  }

  // Preparar los datos de la orden (el usuario se toma de la sesion en microOrders)
  const orderData = {
    products: selectedProducts
  };

  // Enviar los datos de la orden al endpoint
  fetch('/api/orders', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(orderData),
    credentials: 'include'
  })
  .then(response => response.json())
  .then(data => {
    if (data.message === 'Orden creada exitosamente') {
      console.log('Orden creada exitosamente:', data);
      // Mostrar un mensaje de confirmación al usuario
      alert('¡Orden creada exitosamente! (Orden #' + data.order_id + ', total $' + Number(data.total).toFixed(2) + ')');
      // Refrescar el listado para ver el stock descontado
      getProducts();
      if (confirm('¿Quieres ver tus órdenes?')) {
        window.location.href = '/orders';
      }
    } else {
      console.error('Error al crear la orden:', data.message);
      // Mostrar un mensaje de error al usuario
      alert('Error al crear la orden: ' + (data.message || 'Intenta nuevamente.'));
    }
  })
  .catch(error => {
    console.error('Error:', error);
    alert('Ocurrió un error al procesar la orden. Por favor, intenta nuevamente.');
  });
}
