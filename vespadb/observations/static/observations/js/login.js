const { createApp } = Vue;

createApp({
    data() {
        return {
            username: '',
            password: ''
        };
    },
    methods: {
        async login() {
            try {
                const response = await fetch('/api-token-auth/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username: this.username, password: this.password }),
                });

                if (!response.ok) {
                    throw new Error('Login failed.');
                }

                const data = await response.json();
                localStorage.setItem('token', data.token);

                // Redirect to the dashboard page or wherever appropriate
                window.location.href = '/map/';
            } catch (error) {
                alert('Login failed. Please try again.'); // Consider a more user-friendly way to display errors
            }
        }
    }
}).mount('#loginApp');