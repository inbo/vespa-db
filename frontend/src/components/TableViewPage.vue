<template>
    <div class="d-flex flex-column vh-100">
        <NavbarComponent />
        <div class="flex-grow-1 position-relative">
            <button class="btn-filter-toggle" @click="toggleFilterPane">
                <i class="fas fa-sliders-h"></i> Filters
            </button>
            <div class="filter-panel" :class="{ 'panel-active': isFilterPaneOpen }">
                <FilterComponent />
            </div>
            <div class="container mt-4">
                <TableViewComponent></TableViewComponent>
            </div>
        </div>
    </div>
</template>

<script>
import { useVespaStore } from '@/stores/vespaStore';
import { ref } from 'vue';
import FilterComponent from './FilterComponent.vue';
import NavbarComponent from './NavbarComponent.vue';
import TableViewComponent from './TableViewComponent.vue';

export default {
    components: {
        NavbarComponent,
        TableViewComponent,
        FilterComponent
    },
    setup() {
        const vespaStore = useVespaStore();
        const isFilterPaneOpen = ref(false);

        const toggleFilterPane = () => {
            isFilterPaneOpen.value = !isFilterPaneOpen.value;
        };

        return { toggleFilterPane, isFilterPaneOpen };
    },
}
</script>
  