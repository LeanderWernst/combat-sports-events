<script setup lang="ts">
import SubscriptionView from './SubscriptionView.vue';
import EventTable from '../components/EventTable.vue'

const years = [2024, 2025, 2026]
const ical_files = ['ufc_events.ics', 'glory_events.ics', 'one_events.ics'];
const json_files = ['ufc.json', 'glory.json', 'one.json'];
</script>

<template>
  <main class="main">
    <EventTable :json_files=json_files :years=years />
    <SubscriptionView :ical_files=ical_files class="landscape-hidden" />
  </main>
</template>
<style>
.main {
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
}
</style>
