<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
import Headline from './components/Headline.vue'
import Toast from 'primevue/toast';
import { onMounted } from 'vue';

/* onMounted(() => {
  document.addEventListener('gesturestart', (event) => {
      event.preventDefault();
  });

  let lastTouchEnd = 0;

  document.addEventListener('touchend', (event) => {
      const now = Date.now();
      if (now - lastTouchEnd <= 300) {
          event.preventDefault();
      }
      lastTouchEnd = now;
  }, false);
}); */
</script>

<template>
  <header>
    <div class="wrapper">
      <Headline msg="combat cal" class="landscape-hidden" />
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
