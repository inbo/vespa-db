<template>
    <div class="loader">
        <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Observaties worden geladen..</span>
        </div>
    </div>
</template>

<script>
export default {
    name: "Loader"
};
</script>

<style scoped>
.loader {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
}
</style>