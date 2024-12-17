<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
import Headline from './components/Headline.vue'
import Toast from 'primevue/toast';
</script>

<template>
  <header>
    <div class="wrapper">
      <Headline msg="combat cal" />
      <Toast />
      <!-- <nav>
        <RouterLink to="/">Home</RouterLink>
        <RouterLink to="/about">About</RouterLink>
      </nav> -->
    </div>
  </header>
  <RouterView />
</template>

<style scoped>
</style>
