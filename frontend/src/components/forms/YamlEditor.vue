<template>
  <div class="overflow-hidden rounded-2xl border border-console-edge bg-console-deep/70">
    <div class="flex items-center justify-between border-b border-console-edge/70 px-4 py-2 text-xs uppercase tracking-[0.18em] text-console-muted">
      <span>YAML Editor</span>
      <span>{{ editorMode }}</span>
    </div>
    <div v-if="fallbackMode" class="border-b border-amber-500/20 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
      Monaco could not be initialized in this browser session. Falling back to a plain text editor.
    </div>
    <div v-show="!fallbackMode" ref="editorElement" class="min-h-[380px] w-full" />
    <textarea
      v-if="fallbackMode"
      v-model="fallbackValue"
      class="min-h-[380px] w-full resize-y bg-transparent px-4 py-3 font-mono text-sm text-slate-100 outline-none"
      spellcheck="false"
      autocapitalize="off"
      autocomplete="off"
      autocorrect="off"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = withDefaults(
  defineProps<{
    modelValue: string
    height?: number
    readOnly?: boolean
  }>(),
  {
    height: 380,
    readOnly: false,
  },
)

const emit = defineEmits(['update:modelValue'])

const editorElement = ref<HTMLElement | null>(null)
const fallbackMode = ref(false)
const fallbackValue = ref(props.modelValue)
const editorMode = computed(() => (fallbackMode.value ? 'Fallback' : 'Monaco'))

let editorInstance: any = null
let modelInstance: any = null
let applyingExternalValue = false
let resizeObserver: ResizeObserver | null = null

watch(
  () => props.modelValue,
  (value) => {
    fallbackValue.value = value
    if (!modelInstance || applyingExternalValue) {
      return
    }
    if (modelInstance.getValue() !== value) {
      modelInstance.setValue(value)
    }
  },
)

watch(fallbackValue, (value) => {
  if (fallbackMode.value) {
    emit('update:modelValue', value)
  }
})

async function setupMonaco() {
  if (!editorElement.value) return

  try {
    await import('monaco-editor/esm/vs/basic-languages/yaml/yaml.contribution')
    const monaco = await import('monaco-editor/esm/vs/editor/editor.api')

    monaco.editor.defineTheme('ansible-console', {
      base: 'vs-dark',
      inherit: true,
      rules: [
        { token: 'string', foreground: '8DEBFF' },
        { token: 'keyword', foreground: '58D2D9' },
        { token: 'number', foreground: 'F6C177' },
      ],
      colors: {
        'editor.background': '#0f1b2b',
        'editorLineNumber.foreground': '#4e6787',
        'editorLineNumber.activeForeground': '#e7eff7',
        'editorIndentGuide.background1': '#223149',
        'editor.selectionBackground': '#23496f',
        'editor.inactiveSelectionBackground': '#19314b',
      },
    })

    modelInstance = monaco.editor.createModel(props.modelValue, 'yaml')
    editorInstance = monaco.editor.create(editorElement.value, {
      model: modelInstance,
      automaticLayout: true,
      minimap: { enabled: false },
      fontSize: 13,
      lineHeight: 20,
      padding: { top: 12, bottom: 12 },
      wordWrap: 'on',
      roundedSelection: true,
      scrollBeyondLastLine: false,
      readOnly: props.readOnly,
      theme: 'ansible-console',
      overviewRulerBorder: false,
      renderLineHighlight: 'gutter',
      tabSize: 2,
      insertSpaces: true,
    })

    editorElement.value.style.height = `${props.height}px`

    modelInstance.onDidChangeContent(() => {
      if (!modelInstance) return
      applyingExternalValue = true
      emit('update:modelValue', modelInstance.getValue())
      queueMicrotask(() => {
        applyingExternalValue = false
      })
    })

    resizeObserver = new ResizeObserver(() => {
      editorInstance?.layout()
    })
    resizeObserver.observe(editorElement.value)
  } catch {
    fallbackMode.value = true
    await nextTick()
  }
}

onMounted(setupMonaco)

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  modelInstance?.dispose?.()
  editorInstance?.dispose?.()
})
</script>
