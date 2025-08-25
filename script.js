// script.js

document.addEventListener('DOMContentLoaded', () => {
    // Top-level tab buttons (Student/Recruiter)
    const tabButtons = document.querySelectorAll('.tab-button');
    const loginForms = document.querySelectorAll('.login-form');
    const loginHeader = document.querySelector('.login-header');

    // Student sub-tab buttons (Sign In/Create Account)
    const studentSubTabButtons = document.querySelectorAll('.student-sub-tab-button');
    const studentSubForms = document.querySelectorAll('.student-sub-form');

    // Student Forms
    const studentSignInForm = document.getElementById('studentSignInForm');
    const newStudentNameInput = document.getElementById('newStudentName');
    const newStudentEmailInput = document.getElementById('newStudentEmail');
    const newStudentPasswordInput = document.getElementById('newStudentPassword');
    const confirmStudentPasswordInput = document.getElementById('confirmStudentPassword');
    const studentCreateAccountForm = document.getElementById('studentCreateAccountForm');

    // Recruiter Form
    const recruiterForm = document.getElementById('recruiterForm');

    // --- Functions for Top-Level Tabs (Student/Recruiter) ---
    function activateTab(tabName) {
        tabButtons.forEach(button => button.classList.remove('active'));
        loginForms.forEach(form => form.classList.remove('active'));

        const activeButton = document.querySelector(`.tab-button[data-tab="${tabName}"]`);
        if (activeButton) {
            activeButton.classList.add('active');
        }

        const activeForm = document.getElementById(`${tabName}-login-form`);
        if (activeForm) {
            activeForm.classList.add('active');
        }

        if (loginHeader) {
            if (tabName === 'recruiter') {
                loginHeader.classList.add('recruiter-active');
            } else {
                loginHeader.classList.remove('recruiter-active');
            }
        }
    }

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.dataset.tab;
            activateTab(tabName);
            // When switching to student tab, ensure 'Sign In' is active by default
            if (tabName === 'student') {
                activateStudentSubTab('signIn');
            }
        });
    });

    // --- Functions for Student Sub-Tabs (Sign In / Create Account) ---
    function activateStudentSubTab(subTabName) {
        studentSubTabButtons.forEach(button => button.classList.remove('active'));
        studentSubForms.forEach(form => form.classList.remove('active'));

        const activeSubButton = document.querySelector(`.student-sub-tab-button[data-sub-tab="${subTabName}"]`);
        if (activeSubButton) {
            activeSubButton.classList.add('active');
        }

        const activeSubForm = document.getElementById(`student${subTabName.charAt(0).toUpperCase() + subTabName.slice(1)}Form`);
        if (activeSubForm) {
            activeSubForm.classList.add('active');
        }
    }

    studentSubTabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const subTabName = button.dataset.subTab;
            activateStudentSubTab(subTabName);
        });
    });

    // --- Handle Student Sign In Form Submission ---
    studentSignInForm.addEventListener('submit', (event) => {
        event.preventDefault();
        const email = document.getElementById('studentEmail').value;
        const password = document.getElementById('studentPassword').value;

        if (email === '' || password === '') {
            alert('Please fill in both email and password for Student Sign In.');
            return;
        }

        console.log('Student Sign In Attempt:');
        console.log('Email:', email);
        console.log('Password:', password);

        localStorage.setItem('studentEmail', email);

        alert('Student sign in successful! Redirecting to dashboard...');
        setTimeout(() => {
            window.location.href = '/student-dashboard.html';
        }, 500);
    });

    // --- Handle Student Create Account Form Submission ---
    studentCreateAccountForm.addEventListener('submit', (event) => {
        event.preventDefault();
        const name = newStudentNameInput.value.trim();
        const email = newStudentEmailInput.value.trim();
        const password = newStudentPasswordInput.value;
        const confirmPassword = confirmStudentPasswordInput.value;

        if (name === '' || email === '' || password === '' || confirmPassword === '') {
            alert('Please fill in all fields to create a new account.');
            return;
        }

        if (password !== confirmPassword) {
            alert('Passwords do not match. Please re-enter.');
            return;
        }

        if (password.length < 6) {
            alert('Password must be at least 6 characters long.');
            return;
        }

        console.log('Student Create Account Attempt:');
        console.log('Name:', name);
        console.log('Email:', email);
        console.log('Password:', password);

        localStorage.setItem('studentEmail', email);
        localStorage.setItem('studentProfileData', JSON.stringify({
            name: name,
            email: email,
            major: "Not specified",
            status: "New User"
        }));

        alert('New student account created successfully! Redirecting to dashboard...');
        setTimeout(() => {
            window.location.href = '/student-dashboard.html';
        }, 500);
    });

    // --- Handle Recruiter Form Submission ---
    recruiterForm.addEventListener('submit', (event) => {
        event.preventDefault();
        const email = document.getElementById('recruiterEmail').value;
        const password = document.getElementById('recruiterPassword').value;

        if (email === '' || password === '') {
            alert('Please fill in both email and password for Recruiter Login.');
            return;
        }

        console.log('Recruiter Login Attempt:');
        console.log('Email:', email);
        console.log('Password:', password);

        alert('Recruiter login successful! Redirecting to dashboard...');
        setTimeout(() => {
            window.location.href = '/recruiter-dashboard.html';
        }, 500);
    });

    // Initial activation
    activateTab('student');
    activateStudentSubTab('signIn');
});
