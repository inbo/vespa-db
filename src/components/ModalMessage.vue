<template>
    <div v-if="isVisible" class="modal-overlay">
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-11 col-sm-8 col-md-6 col-lg-5 col-xl-4 modal-content">
                    <h5>{{ title }}</h5>
                    <p>{{ message }}</p>
                    <button @click="closeModal" class="btn btn-success">OK</button>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    props: {
        title: String,
        message: String,
        isVisible: Boolean
    },
    methods: {
        closeModal() {
            this.$emit('close');
        }
    }
};
</script>

<style scoped>
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(0, 0, 0, 0.5);
    z-index: 2000;
}

.modal-content {
    background: white;
    padding: 20px;
    border-radius: 5px;
    text-align: center;
}
</style>