// Example: Handle login form submission
const loginForm = document.getElementById('loginForm');
loginForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const username = document.getElementById('username').value;
  const password = document.getElementById('password').value;

  try {
    const response = await fetch('/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ username, password })
    });

    if (response.ok) {
      // Login successful, redirect or update the UI
      console.log('Login successful');
    } else {
      // Login failed, display an error message
      console.error('Login failed');
    }
  } catch (error) {
    console.error('Error during login:', error);
  }
});





fetch('/employees')
  .then(response => response.json())
  .then(data => {
    // Populate the employee table or display the data
    console.log(data);
  })
  .catch(error => {
    console.error('Error fetching employee data:', error);
  });
