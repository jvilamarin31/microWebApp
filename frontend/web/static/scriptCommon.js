function logout() {
  fetch('/api/logout', {
    method: 'POST',
    credentials: 'include'
  })
  .then(() => {
    window.location.href = '/';
  })
  .catch(error => {
    console.error('Logout error:', error);
    window.location.href = '/';
  });
}
