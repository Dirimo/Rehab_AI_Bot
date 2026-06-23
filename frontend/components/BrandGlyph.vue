<script setup lang="ts">
withDefaults(defineProps<{ size?: number }>(), { size: 80 })
</script>

<template>
  <BrandLogo3d :size="size" :rotate="true" />
</template>
