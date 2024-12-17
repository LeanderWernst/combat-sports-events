<script setup lang="ts">
import SubscriptionView from './SubscriptionView.vue';
import EventTable from '../components/EventTable.vue'

const years = [2024, 2025, 2026]
const ical_files = ['ufc_events.ics', 'glory_events.ics'];
const json_files = ['ufc.json', 'glory.json']
</script>

<template>
  <main>
    <EventTable :json_files=json_files :years=years />
    <SubscriptionView :ical_files=ical_files />
  </main>
</template>
