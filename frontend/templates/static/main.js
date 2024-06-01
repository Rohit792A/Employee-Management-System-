// Function to fetch employee data
async function fetchEmployeeData() {
  try {
    const response = await fetch('http://127.0.0.1:8000/employees', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (response.ok) {
      const employees = await response.json();
      displayEmployeeData(employees);
    } else {
      console.error('Failed to fetch employee data');
    }
  } catch (error) {
    console.error('Error fetching employee data:', error);
  }
}

// Function to display employee data
function displayEmployeeData(employees) {
  const employeeList = document.getElementById('employeeList');
  employeeList.innerHTML = '';

  employees.forEach(employee => {
    const listItem = document.createElement('li');
    listItem.textContent = `Name: ${employee.name}, Email: ${employee.email}, User Type: ${employee.userType}`;
    employeeList.appendChild(listItem);
  });
}

// Add event listener to the button
const fetchEmployeeDataBtn = document.getElementById('fetchEmployeeDataBtn');
fetchEmployeeDataBtn.addEventListener('click', fetchEmployeeData);









// function handleEmployeeFormSubmit(event) {
//   const formData = {
//     name: document.getElementById('name').value,
//     email: document.getElementById('email').value,
//     user_type: document.getElementById('user_type').value,
//     password: document.getElementById('password').value,

//   };

//   try {
//     const response = fetch('/employees/', {
//       method: 'POST',
//       headers: {
//         'Content-Type': 'application/json'
//       },
//       body: JSON.stringify(formData)
//     });

//     if (response.ok) {
//       // Employee creation successful, display a success message or redirect
//       console.log('Employee created successfully');
//     } else {
//       // Employee creation failed, display an error message
//       console.error('Failed to create employee');
//     }
//   } catch (error) {
//     console.error('Error creating employee:', error);
//   }
// }
  


// document.querySelector('form').addEventListener('submit', function(event) {
//   document.querySelector('form').addEventListener('submit', function(event) {
//     event.preventDefault();
  
//     const formData = {
//       name: document.querySelector('#name').value,
//       email: document.querySelector('#email').value,
//       user_type: document.querySelector('#user_type').value,
//       password: document.querySelector('#password').value
//     };
  
//     const formattedData = [formData];
  
//     console.log(formattedData);
//   })});