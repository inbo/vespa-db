<template>
    <div id="filters">
      <div class="filter-item" v-for="(filter, key) in filters" :key="key">
        <label :for="key">{{ filter.label }}</label>
        <input
          v-if="filter.type === 'date'"
          type="date"
          :id="key"
          v-model="filter.value"
          @change="applyFilter"
        />
      </div>
    </div>
  </template>
  
  <script>
  export default {
    name: 'FilterComponent',
    props: ['initialFilters'],
    data() {
      return {
        filters: this.initialFilters,
      };
    },
    methods: {
      applyFilter() {
        this.$emit('updateFilters', this.filters);
      },
    },
  };
  </script>
  
  <style scoped>
  #filters {
      background-color: #f4f4f4;
      padding: 20px;
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      border-bottom: 2px solid #ddd;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }
  
  .filter-item {
      display: flex;
      align-items: center;
      gap: 10px;
  }
  
  .filter-item label {
      font-weight: bold;
      margin: 0;
      white-space: nowrap;
  }
  
  .filter-item input[type="date"] {
      padding: 8px;
      border: 1px solid #ccc;
      border-radius: 4px;
      font-size: 16px;
      color: #333;
  }
  
  .filter-item input[type="date"]:focus {
      outline: none;
      border-color: #007bff;
      box-shadow: 0 0 0 0.2rem rgba(0,123,255,.25);
  }
  </style>