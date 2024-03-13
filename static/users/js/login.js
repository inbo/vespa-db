const { createApp } = Vue;

createApp({
    data() {
        return {
            username: '',
            password: ''
        };
    },
    methods: {
        getCsrfToken() {
            return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        },
        async login() {
            try {
                const csrfToken = this.getCsrfToken();
                const response = await fetch('/login/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                    },
                    body: JSON.stringify({ username: this.username, password: this.password }),
                });

                if (!response.ok) {
                    throw new Error('Login failed.');
                }

                window.location.href = '/map/';
            } catch (error) {
                alert('Login failed. Please try again.');
            }
        }
    }
}).mount('#loginApp');
