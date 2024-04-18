<template>
  <div id="app">
    <router-view v-slot="{ Component }">
      <keep-alive include="MapPage">
        <component :is="Component" />
      </keep-alive>
    </router-view>
  </div>
</template>
<script>
export default {
  name: 'App',
  created() { },
  components: {
  }
}
</script>
