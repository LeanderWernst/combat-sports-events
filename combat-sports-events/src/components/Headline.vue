<script setup lang="ts">
defineProps<{
  msg: string
}>()
</script>

<template>
  <div class="">
    <h1 class="red">{{ msg }}</h1>
  </div>
</template>

<style scoped>
h1 {
  text-align: center;
  text-transform: uppercase;
  font-weight: bold;
  font-size: 2rem;
}
</style>
