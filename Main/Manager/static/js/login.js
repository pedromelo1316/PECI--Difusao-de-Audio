function audioRegister() {
  const name = document.getElementById('registerName').value;
  const email = document.getElementById('registerEmail').value;
  const password = document.getElementById('registerPassword').value;
  const confirmPassword = document.getElementById('confirmPassword').value;

  if (password !== confirmPassword) {
    alert('Passwords do not match!');
    return;
  }

  fetch('/register', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ name, email, password }),
  })
    .then((response) => {
      if (response.ok) {
        window.location.href = '/login'; // Redirect to login page
      } else {
        response.json().then((data) => alert(data.error || 'Registration failed!'));
      }
    })
    .catch((error) => {
      console.error('Error:', error);
      alert('An error occurred during registration.');
    });
}

function audioLogin() {
  const email = document.getElementById('loginEmail').value;
  const password = document.getElementById('loginPassword').value;

  fetch('/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  })
    .then((response) => {
      if (response.ok) {
        response.json().then((data) => {
          if (data.redirectUrl) {
            window.location.href = data.redirectUrl; // Redirect to the URL provided by the server
          } else {
            console.log('Login successful, but no redirect URL provided');
          }
        });
      } else {
        response.json().then((data) => alert(data.error || 'Login failed!'));
      }
    })
    .catch((error) => {
      console.error('Error:', error);
      alert('An error occurred during login.');
    });
}


document.addEventListener('DOMContentLoaded', function() {
  // Set up for login form
  const loginInputs = ['loginEmail', 'loginPassword'];
  loginInputs.forEach(id => {
    const element = document.getElementById(id);
    if (element) {
      element.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
          e.preventDefault();
          audioLogin();
        }
      });
    }
  });
  
  
  const registerInputs = ['registerName', 'registerEmail', 'registerPassword', 'confirmPassword'];
  registerInputs.forEach(id => {
    const element = document.getElementById(id);
    if (element) {
      element.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
          e.preventDefault();
          audioRegister();
        }
      });
    }
  });
});