<script setup>
defineProps({
  eyebrow: { type: String, required: true },
  title: { type: String, required: true }
})
</script>

<template>
  <div class="min-w-0">
    <div class="flex items-center gap-2">
      <span class="inline-block size-2 shrink-0 rounded-full bg-brand" aria-hidden="true"></span>
      <p class="text-[10px] font-semibold uppercase tracking-widest text-brand">{{ eyebrow }}</p>
    </div>
    <h1 class="mt-1 text-[22px] font-bold leading-tight tracking-tight text-ink sm:text-[26px]">{{ title }}</h1>
  </div>
</template>
