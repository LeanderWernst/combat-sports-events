<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
import Headline from './components/Headline.vue'
</script>

<template>
  <header>
    <div class="wrapper">
      <Headline msg="combat cal" />
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
