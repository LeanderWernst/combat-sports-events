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
  text-transform: lowercase;
  font-family: 'UFC';
  font-weight: bold;
  font-size: 2em;
  letter-spacing: 4px;
  color: whitesmoke;
  line-height: normal;
  margin-top: 1%;
}
</style>
