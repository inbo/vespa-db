// src/services/apiService.js
import axios from 'axios';

const API_URL = import.meta.env.VITE_APP_API_URL;

const ApiService = {
    getAxiosInstance() {
        const instance = axios.create({
            baseURL: API_URL,
            withCredentials: true,
        });

        const accessToken = localStorage.getItem('access_token');
        if (accessToken) {
            instance.defaults.headers.common["Authorization"] = `Bearer ${accessToken}`;
        }

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
