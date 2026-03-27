<template>
  <section class="overflow-hidden rounded-3xl border border-console-edge bg-console-panel/70 shadow-xl shadow-slate-950/20">
    <div v-if="title || description || $slots.toolbar" class="flex flex-col gap-3 border-b border-console-edge/70 px-5 py-4 md:flex-row md:items-center md:justify-between">
      <div>
        <h3 v-if="title" class="text-base font-semibold text-white">{{ title }}</h3>
        <p v-if="description" class="mt-1 text-sm text-console-muted">{{ description }}</p>
      </div>
      <div v-if="$slots.toolbar" class="flex flex-wrap gap-2">
        <slot name="toolbar" />
      </div>
    </div>

    <div v-if="loading" class="px-5 py-10">
      <div class="rounded-2xl border border-console-edge bg-console-deep/40 px-5 py-8">
        <div class="h-3 w-32 rounded-full bg-console-edge/80" />
        <div class="mt-5 space-y-3">
          <div class="h-10 rounded-2xl bg-console-deep/80" />
          <div class="h-10 rounded-2xl bg-console-deep/70" />
          <div class="h-10 rounded-2xl bg-console-deep/60" />
        </div>
        <p class="mt-5 text-sm font-semibold text-white">{{ loadingTitle }}</p>
        <p v-if="loadingDescription" class="mt-2 max-w-xl text-sm text-console-muted">{{ loadingDescription }}</p>
      </div>
    </div>

    <div v-else-if="rows.length" class="overflow-x-auto">
      <table class="min-w-full divide-y divide-console-edge/70 text-sm">
        <thead class="bg-console-deep/60 text-console-muted">
          <tr>
            <th
              v-for="column in columns"
              :key="column.key"
              class="px-4 py-3 text-left font-medium uppercase tracking-[0.18em]"
              :class="compact ? 'text-[11px]' : 'text-xs'"
            >
              {{ column.label }}
            </th>
            <th v-if="$slots.actions" class="px-4 py-3 text-right font-medium uppercase tracking-[0.18em]" :class="compact ? 'text-[11px]' : 'text-xs'">
              Actions
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in rows"
            :key="row[rowKey]"
            class="border-t border-console-edge/60 transition hover:bg-console-deep/40"
          >
            <td
              v-for="column in columns"
              :key="column.key"
              class="align-top text-console-ink/95"
              :class="compact ? 'px-4 py-3' : 'px-4 py-4'"
            >
              <slot :name="column.key" :row="row">{{ row[column.key] }}</slot>
            </td>
            <td v-if="$slots.actions" class="px-4 py-3 text-right align-top">
              <slot name="actions" :row="row" />
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else class="px-5 py-10">
      <slot name="empty">
        <div class="rounded-2xl border border-dashed border-console-edge bg-console-deep/40 px-5 py-8 text-center">
          <p class="text-sm font-semibold text-white">{{ emptyTitle }}</p>
          <p v-if="emptyDescription" class="mx-auto mt-2 max-w-xl text-sm text-console-muted">{{ emptyDescription }}</p>
        </div>
      </slot>
    </div>
  </section>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    columns: Array<{ key: string; label: string }>
    rows: Array<Record<string, any>>
    rowKey?: string
    title?: string
    description?: string
    emptyTitle?: string
    emptyDescription?: string
    compact?: boolean
    loading?: boolean
    loadingTitle?: string
    loadingDescription?: string
  }>(),
  {
    rowKey: 'id',
    title: undefined,
    description: undefined,
    emptyTitle: 'No records found',
    emptyDescription: undefined,
    compact: false,
    loading: false,
    loadingTitle: 'Loading records',
    loadingDescription: 'The latest operator data is being collected.',
  },
)
</script>
