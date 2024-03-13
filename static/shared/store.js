export const store = {
    state: {
        isLoggedIn: false,
        username: '',
        userId: null
    },
    setLoginStatus(isLoggedIn, username, userId) {
        this.state.isLoggedIn = isLoggedIn;
        this.state.username = username;
        this.state.userId = userId;
    },
    checkLoginStatus: async function () {
        try {
            const response = await fetch('/check_login/', {
                method: 'GET',
                credentials: 'include'
            });
            if (response.ok) {
                const data = await response.json();
                this.setLoginStatus(data.isLoggedIn, data.username, data.user_id);
                console.log("Login status from store: ", this.state.isLoggedIn);
            } else {
                this.setLoginStatus(false, '', null);
            }
        } catch (error) {
            console.error('Error checking login status:', error);
            this.setLoginStatus(false, '', null);
        }
    },
    logout() {
        fetch('/logout/', {
            method: 'POST',
            credentials: 'include'
        }).then(() => {
            this.setLoginStatus(false, '', null);
            window.location.href = '/login/';
        }).catch(error => console.error('Logout failed:', error));
    },
};
