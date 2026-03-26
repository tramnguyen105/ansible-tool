<template>
  <div class="overflow-hidden rounded-2xl border border-console-edge bg-console-deep/70">
    <MonacoEditor v-model:value="model" height="380px" language="yaml" theme="vs-dark" :options="options" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { MonacoEditor } from '@guolao/vue-monaco-editor'

const props = defineProps<{ modelValue: string }>()
const emit = defineEmits(['update:modelValue'])

const model = computed({
  get: () => props.modelValue,
  set: (value: string) => emit('update:modelValue', value),
})

const options = {
  minimap: { enabled: false },
  fontSize: 13,
  wordWrap: 'on',
  automaticLayout: true,
}
</script>
