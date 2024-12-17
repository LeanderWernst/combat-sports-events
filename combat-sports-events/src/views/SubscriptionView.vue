<script setup lang="ts">
import SubscribePopover from '../components/SubscribePopover.vue';

const props = defineProps<{
    ical_files: string[];
}>();
</script>

<template>
    <div class="popover_container">
        <SubscribePopover v-for="file of props.ical_files" :file=file />
    </div>
</template>

<style>
    .popover_container {
        display: flex;
        flex-direction: row;
    }

    .popover_container > div {
        margin: 1rem 0.5rem;
    }
</style>