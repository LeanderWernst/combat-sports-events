<script setup lang="ts">
import SubscriptionView from './SubscriptionView.vue';
import EventTable from '../components/EventTable.vue'

const files = ['ufc_events.ics', 'glory_events.ics'];
</script>

<template>
  <main>
    <EventTable :files=files />
    <SubscriptionView :files=files />
  </main>
</template>
