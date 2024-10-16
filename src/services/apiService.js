// src/services/apiService.js
import axios from 'axios';

const API_URL = import.meta.env.VITE_APP_API_URL;
const instance = axios.create({
    baseURL: API_URL,
    withCredentials: true,
});

function getCookie(name) {
    const value = '; ' + document.cookie;
    const parts = value.split('; ' + name + '=');
    if (parts.length === 2) return parts.pop().split(';').shift() || null;
    return null;
}


const ApiService = {
    getAxiosInstance() {
        instance.interceptors.request.use((config) => {
            const csrfToken = getCookie('csrftoken');
            if (csrfToken) {
                config.headers['X-CSRFToken'] = csrfToken;
            }
            return config;
        });
        return instance;
    },

    get(resource) {
        return this.getAxiosInstance().get(resource);
    },

    post(resource, data) {
        return this.getAxiosInstance().post(resource, data);
    },

    patch(resource, data) {
        return this.getAxiosInstance().patch(resource, data);
    },

    delete(resource) {
        return this.getAxiosInstance().delete(resource);
    },
};

export default ApiService;
