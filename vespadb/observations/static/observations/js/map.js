const app = Vue.createApp({
    data() {
        return {
            selectedObservation: null,
            isLoggedIn: !!localStorage.getItem('token'),
            isEditing: false,
            username: '',
            observations: [],
            map: null,
            markers: [],
        };
    },
    methods: {
        selectObservation(observationData) {
            // Select a observation for viewing or editing
            this.selectedObservation = observationData;
        },
        async getObservations() {
            // Fetch observations data from the server
            try {
                const response = await fetch('/observations/');
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                const data = await response.json();
                this.observations = data;
                if (!this.map) {
                    this.initializeMapAndMarkers(); // Initialize map after fetching observations for the first time
                } else {
                    this.updateMarkers(); // Update markers based on new observations data
                }
            } catch (error) {
                console.error('There has been a problem with your fetch operation:', error);
            }
        },
        initializeMapAndMarkers() {
            // Initialize map and place markers for each observation
            this.map = L.map('mapid').setView([51.0, 4.5], 9);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: 'Map data © OpenStreetMap contributors',
                maxZoom: 18,
            }).addTo(this.map);
            this.updateMarkers();
        },
        updateMarkers() {
            // Clear existing markers
            this.markers.forEach(marker => this.map.removeLayer(marker));
            this.markers = []; // Reset markers array

            // Add new markers based on observations data
            this.observations.forEach((observation) => {
                const locationRegex = /POINT \(([^ ]+) ([^ ]+)\)/;
                const match = observation.location.match(locationRegex);
                if (match) {
                    const [_, longitude, latitude] = match; // Destructure to get longitude and latitude
                    const marker = L.marker([parseFloat(latitude), parseFloat(longitude)], {
                        icon: L.divIcon({
                            className: 'custom-div-icon',
                            html: "<i class='fa fa-bug' style='color: black; font-size: 24px;'></i>",
                            iconSize: [30, 42],
                            iconAnchor: [15, 42]
                        })
                    }).addTo(this.map)
                        .on('click', () => this.selectObservation(observation));
                    this.markers.push(marker); // Store marker reference
                }
            });
        },
        async updateObservation() {
            // Update observation information on the server
            try {
                const response = await fetch(`/observations/${this.selectedObservation.id}/`, {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Token ${localStorage.getItem('token')}`,
                    },
                    body: JSON.stringify(this.selectedObservation)
                });
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                const data = await response.json();
                console.log('Success:', data);
                this.isEditing = false; // End editing after successful update
            } catch (error) {
                console.error('Error when updating the observation:', error);
            }
        },
        async login() {
            // Handle user login
            try {
                const response = await fetch('/api-token-auth/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        username: this.username,
                        password: this.password,
                    }),
                });
                if (!response.ok) {
                    throw new Error('Login failed.');
                }
                const data = await response.json();
                localStorage.setItem('token', data.token);
                this.username = '';
                this.password = '';
                this.closeLoginModal(); // Close modal on successful login
                this.isLoggedIn = true;
            } catch (error) {
                throw new Error('Login failed. Please try again.');
            }
        },
        logout() {
            // Handle user logout
            localStorage.removeItem('token');
            this.isLoggedIn = false;
        },
        startEdit() {
            // Enable edit mode
            this.isEditing = true;
        },
    },
    mounted() {
        this.getObservations(); // Initial fetch
        setInterval(this.getObservations, 60000); // Poll every 60 seconds
    }
});
app.mount('#app');