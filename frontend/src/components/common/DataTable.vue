<template>
  <div class="overflow-hidden rounded-3xl border border-console-edge bg-console-panel/70">
    <table class="min-w-full divide-y divide-console-edge/70 text-sm">
      <thead class="bg-console-deep/60 text-console-muted">
        <tr>
          <th v-for="column in columns" :key="column.key" class="px-4 py-3 text-left font-medium">{{ column.label }}</th>
          <th v-if="$slots.actions" class="px-4 py-3 text-right font-medium">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="row[rowKey]" class="border-t border-console-edge/60">
          <td v-for="column in columns" :key="column.key" class="px-4 py-3 align-top text-console-ink/95">
            <slot :name="column.key" :row="row">{{ row[column.key] }}</slot>
          </td>
          <td v-if="$slots.actions" class="px-4 py-3 text-right">
            <slot name="actions" :row="row" />
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
defineProps<{ columns: Array<{ key: string; label: string }>; rows: Array<Record<string, any>>; rowKey?: string }>()
</script>
