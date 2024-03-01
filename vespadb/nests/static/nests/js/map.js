const app = Vue.createApp({
    data() {
        return {
            selectedNest: null,
            isLoggedIn: !!localStorage.getItem('token'),
            isEditing: false,
            username: '',
            password: '',
            nests: [],
        };
    },
    methods: {
        selectNest(nestData) {
            this.selectedNest = nestData;
        },
        getNests() {
            return fetch('/nests/')
                .then(response => {
                    if (!response.ok) {
                        console.error('Network response was not ok', response);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('Data:', data);
                    this.nests = data;
                    this.initializeMapAndMarkers();
                })
                .catch(error => {
                    console.error('There has been a problem with your fetch operation:', error);
                });
        },
        initializeMapAndMarkers() {
            var mymap = L.map('mapid').setView([51.0, 4.5], 9);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: 'Map data © OpenStreetMap contributors',
                maxZoom: 18,
            }).addTo(mymap);

            this.nests.forEach((nest) => {
                const locationRegex = /POINT \(([^ ]+) ([^ ]+)\)/;
                const match = nest.location.match(locationRegex);
                if (match) {
                    const longitude = parseFloat(match[1]);
                    const latitude = parseFloat(match[2]);
                    var marker = L.marker([latitude, longitude], {
                        icon: L.divIcon({
                            className: 'custom-div-icon',
                            html: "<i class='fa fa-bug' style='color: black; font-size: 24px;'></i>",
                            iconSize: [30, 42],
                            iconAnchor: [15, 42]
                        })
                    }).addTo(mymap);
                    marker.bindPopup(`<b>Nest Status:</b> ${nest.status}`);
                    marker.on('click', () => this.selectNest(nest));
                }
            });
        },
        confirmUpdate() {
            fetch(`/nests/${this.selectedNest.id}/`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Token ${localStorage.getItem('token')}`,
                },
                body: JSON.stringify(this.selectedNest)
            })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Netwerk response was niet ok');
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('Succes:', data);
                })
                .catch(error => {
                    console.error('Error when updating the nest:', error);
                });
        },
        login() {
            fetch('/api-token-auth/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username: this.username,
                    password: this.password,
                }),
            })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Login failed.');
                    }
                    return response.json();
                })
                .then(data => {
                    localStorage.setItem('token', data.token);
                    this.username = '';
                    this.password = '';
                    var modal = document.getElementById('loginModal');
                    modal.style.display = 'none';
                    this.isLoggedIn = true;
                })
                .catch(error => {
                    alert('Login failed. Please try again.');
                });
        },
        logout() {
            localStorage.removeItem('token');
            this.isLoggedIn = false;
        },
        startEdit() {
            this.isEditing = true;
        },
        confirmUpdate() {
            this.isEditing = false;
        },

    },
    mounted() {
        this.getNests();
    }
});
app.mount('#app');

function showLoginModal() {
    document.getElementById('loginModal').style.display = 'block';
}

function closeLoginModal() {
    document.getElementById('loginModal').style.display = 'none';
}