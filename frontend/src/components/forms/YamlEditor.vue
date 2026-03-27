<template>
  <div class="overflow-hidden rounded-2xl border border-console-edge bg-console-deep/70">
    <textarea
      v-model="model"
      class="min-h-[380px] w-full resize-y bg-transparent px-4 py-3 font-mono text-sm text-slate-100 outline-none"
      spellcheck="false"
      autocapitalize="off"
      autocomplete="off"
      autocorrect="off"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ modelValue: string }>()
const emit = defineEmits(['update:modelValue'])

const model = computed({
  get: () => props.modelValue,
  set: (value: string) => emit('update:modelValue', value),
})
</script>
