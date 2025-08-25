document.addEventListener('DOMContentLoaded', () => {
    // Tab switching functionality
    const tabButtons = document.querySelectorAll('.tab-button');
    const loginForms = document.querySelectorAll('.login-form');
    const loginHeader = document.querySelector('.login-header');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetTab = button.dataset.tab;

            // Update active tab button
            tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');

            // Update header animation
            if (targetTab === 'recruiter') {
                loginHeader.classList.add('recruiter-active');
            } else {
                loginHeader.classList.remove('recruiter-active');
            }

            // Show corresponding form
            loginForms.forEach(form => {
                form.classList.remove('active');
                if (form.id === `${targetTab}-login-form`) {
                    form.classList.add('active');
                }
            });
        });
    });

    // Student sub-tab functionality
    const studentSubTabButtons = document.querySelectorAll('.student-sub-tab-button');
    const studentSubForms = document.querySelectorAll('.student-sub-form');

    studentSubTabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetSubTab = button.dataset.subTab;

            // Update active sub-tab button
            studentSubTabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');

            // Show corresponding sub-form
            studentSubForms.forEach(form => {
                form.classList.remove('active');
                if (form.id === `student${targetSubTab.charAt(0).toUpperCase() + targetSubTab.slice(1)}Form`) {
                    form.classList.add('active');
                }
            });
        });
    });

    // Student Sign In Form
    const studentSignInForm = document.getElementById('studentSignInForm');
    if (studentSignInForm) {
        studentSignInForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const email = document.getElementById('studentEmail').value;
            const password = document.getElementById('studentPassword').value;

            try {
                const response = await fetch('/api/login-student', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ email, password }),
                });

                const result = await response.json();

                if (result.success) {
                    localStorage.setItem('studentEmail', email);
                    window.location.href = '/student-dashboard.html';
                } else {
                    alert('Login failed: ' + result.message);
                }
            } catch (error) {
                console.error('Login error:', error);
                alert('An error occurred during login. Please try again.');
            }
        });
    }

    // Student Create Account Form
    const studentCreateAccountForm = document.getElementById('studentCreateAccountForm');
    if (studentCreateAccountForm) {
        studentCreateAccountForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const name = document.getElementById('newStudentName').value;
            const email = document.getElementById('newStudentEmail').value;
            const password = document.getElementById('newStudentPassword').value;
            const confirmPassword = document.getElementById('confirmStudentPassword').value;

            if (password !== confirmPassword) {
                alert('Passwords do not match!');
                return;
            }

            try {
                const response = await fetch('/api/register-student', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ name, email, password }),
                });

                const result = await response.json();

                if (result.success) {
                    alert('Account created successfully! Please sign in.');
                    // Switch to sign in tab
                    document.querySelector('.student-sub-tab-button[data-sub-tab="signIn"]').click();
                } else {
                    alert('Registration failed: ' + result.message);
                }
            } catch (error) {
                console.error('Registration error:', error);
                alert('An error occurred during registration. Please try again.');
            }
        });
    }

    // Recruiter Login Form
    const recruiterForm = document.getElementById('recruiterForm');
    if (recruiterForm) {
        recruiterForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const email = document.getElementById('recruiterEmail').value;
            const password = document.getElementById('recruiterPassword').value;

            try {
                const response = await fetch('/api/login-recruiter', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ email, password }),
                });

                const result = await response.json();

                if (result.success) {
                    window.location.href = '/recruiter-dashboard.html';
                } else {
                    alert('Login failed: ' + result.message);
                }
            } catch (error) {
                console.error('Login error:', error);
                alert('An error occurred during login. Please try again.');
            }
        });
    }

    // AI Prediction functionality for recruiter dashboard
    function initializePredictionForm() {
        const predictionForm = document.getElementById('predictionForm');
        const predictionResult = document.getElementById('predictionResult');

        if (predictionForm) {
            predictionForm.addEventListener('submit', async function(e) {
                e.preventDefault();

                const formData = new FormData(predictionForm);
                const resultDiv = document.getElementById('predictionResult');

                try {
                    resultDiv.innerHTML = '<p>Processing prediction...</p>';

                    const response = await fetch('/predict', {
                        method: 'POST',
                        body: formData
                    });

                    const result = await response.json();

                    if (result.success) {
                        resultDiv.innerHTML = `
                            <div class="prediction-success">
                                <h4>Prediction Result</h4>
                                <p><strong>Decision:</strong> ${result.decision}</p>
                                <p><strong>Match Probability:</strong> ${result.probability}%</p>
                            </div>
                        `;
                    } else {
                        resultDiv.innerHTML = `
                            <div class="prediction-error">
                                <p>Error: ${result.message}</p>
                            </div>
                        `;
                    }
                } catch (error) {
                    console.error('Prediction error:', error);
                    resultDiv.innerHTML = `
                        <div class="prediction-error">
                            <p>An error occurred during prediction. Please try again.</p>
                        </div>
                    `;
                }
            });
        }
    }

    // Initialize prediction form when page loads
    document.addEventListener('DOMContentLoaded', function() {
        initializePredictionForm();
    });
});