const changePasswordApp = Vue.createApp({
    data() {
        return {
            oldPassword: '',
            newPassword: '',
            confirmNewPassword: '',
            token: localStorage.getItem('token'),
        };
    },
    methods: {
        async changePassword() {
            if (this.newPassword !== this.confirmNewPassword) {
                alert("Nieuw wachtwoord komt niet overeen met de bevestiging.");
                return;
            }

            try {
                const response = await fetch(`/api/users/${this.userId}/change_password/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Token ${this.token}`,
                    },
                    body: JSON.stringify({
                        old_password: this.oldPassword,
                        new_password: this.newPassword,
                    }),
                });

                if (!response.ok) {
                    throw new Error('Wachtwoord wijziging mislukt. Probeer het opnieuw.');
                }

                const data = await response.json();
                alert('Wachtwoord succesvol gewijzigd.');
                this.oldPassword = '';
                this.newPassword = '';
                this.confirmNewPassword = '';
                window.location.href = '/map/';
            } catch (error) {
                console.error('Error:', error);
                alert(error.message);
            }
        },
    },
    mounted() {
        if (!(this.token)) {
            console.error('User is not logged in');
            window.location.href = '/map/';
        }
    }
});

changePasswordApp.mount('#changePasswordApp');
