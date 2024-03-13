const profileApp = Vue.createApp({
    data() {
        return {
            username: '',
            userEmail: '',
            userPassword: '',
            userId: null,
            token: localStorage.getItem('token'),
        };
    },
    methods: {
        async fetchUserProfile() {
            try {
                const response = await fetch('/api/user/profile/', {
                    method: 'GET',
                    headers: {
                        'Authorization': `Token ${this.token}`,
                    },
                });
                if (!response.ok) {
                    throw new Error('Failed to fetch profile data');
                }
                const data = await response.json();
                this.username = data.username;
                this.userEmail = data.email;
                this.userId = data.id;
            } catch (error) {
                console.error('Error fetching profile:', error);
            }
        },
        async updateProfile() {
            try {
                const response = await fetch(`/api/users/${this.userId}/`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Token ${this.token}`,
                    },
                    body: JSON.stringify({
                        email: this.userEmail,
                    }),
                });
                if (!response.ok) {
                    throw new Error('Failed to update profile');
                }
                alert('Profile updated successfully');
            } catch (error) {
                console.error('Error updating profile:', error);
            }
        },
        async changePassword() {
            try {
                const response = await fetch(`/api/users/${this.userId}/change_password/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Token ${this.token}`,
                    },
                    body: JSON.stringify({
                        new_password: this.userPassword,
                    }),
                });
                if (!response.ok) {
                    throw new Error('Failed to change password');
                }
                this.userPassword = ''; // Clear the password field after successful change
                alert('Password changed successfully');
            } catch (error) {
                console.error('Error changing password:', error);
            }
        },
        goToChangePasswordPage() {
            window.location.href = '/change-password/';
        },
    },
    mounted() {
        // Fetch the user's profile when the component mounts
        if (this.token) {
            this.fetchUserProfile();
        } else {
            console.error('User is not logged in');
            window.location.href = '/map/';
        }
    }
});

profileApp.mount('#profileApp');