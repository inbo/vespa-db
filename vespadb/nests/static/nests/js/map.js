const app = Vue.createApp({
    data() {
        return {
            selectedNest: null,
            isLoggedIn: !!localStorage.getItem('token'), // Convert string to boolean to determine logged-in state
            isEditing: false,
            username: '',
            password: '',
            nests: [], // Will hold nests data fetched from server
            map: null, // Reference to the map
            markers: [], // Array to keep track of markers
            isModalVisible: false,
        };
    },
    methods: {
        selectNest(nestData) {
            // Select a nest for viewing or editing
            this.selectedNest = nestData;
        },
        async getNests() {
            // Fetch nests data from the server
            try {
                const response = await fetch('/nests/');
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                const data = await response.json();
                this.nests = data;
                if (!this.map) {
                    this.initializeMapAndMarkers(); // Initialize map after fetching nests for the first time
                } else {
                    this.updateMarkers(); // Update markers based on new nests data
                }
            } catch (error) {
                console.error('There has been a problem with your fetch operation:', error);
            }
        },
        initializeMapAndMarkers() {
            // Initialize map and place markers for each nest
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

            // Add new markers based on nests data
            this.nests.forEach((nest) => {
                const locationRegex = /POINT \(([^ ]+) ([^ ]+)\)/;
                const match = nest.location.match(locationRegex);
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
                        .on('click', () => this.selectNest(nest));
                    this.markers.push(marker); // Store marker reference
                }
            });
        },
        async updateNest() {
            // Update nest information on the server
            try {
                const response = await fetch(`/nests/${this.selectedNest.id}/`, {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Token ${localStorage.getItem('token')}`,
                    },
                    body: JSON.stringify(this.selectedNest)
                });
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                const data = await response.json();
                console.log('Success:', data);
                this.isEditing = false; // End editing after successful update
            } catch (error) {
                console.error('Error when updating the nest:', error);
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
        showModal() {
            console.log("Showing login modal");
            this.isModalVisible = true;
        },

        hideModal() {
            console.log("Closing login modal");
            this.isModalVisible = false;
        },
    },
    mounted() {
        this.getNests(); // Initial fetch
        setInterval(this.getNests, 60000); // Poll every 60 seconds
    }
});
app.mount('#app');