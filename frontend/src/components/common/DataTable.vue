<template>
  <section class="rounded-2xl border border-slate-200 bg-white p-5">
    <div class="mb-4 flex items-start justify-between gap-3">
      <div>
        <h3 class="text-[1.15rem] font-semibold text-slate-900">{{ title }}</h3>
        <p v-if="description" class="mt-1 text-[0.96rem] text-slate-600">{{ description }}</p>
      </div>
      <slot name="actions" />
    </div>

    <div v-if="loading" class="rounded-xl border border-dashed border-slate-200 bg-slate-50 px-4 py-8 text-center">
      <p class="text-[0.98rem] font-medium text-slate-900">{{ loadingTitle }}</p>
      <p class="mt-2 text-[0.96rem] text-slate-600">{{ loadingDescription }}</p>
    </div>

    <div v-else-if="error" class="rounded-xl border border-dashed border-rose-200 bg-rose-50 px-4 py-8 text-center">
      <p class="text-[0.98rem] font-medium text-slate-900">{{ errorTitle }}</p>
      <p class="mt-2 text-[0.96rem] text-slate-600">{{ errorDescription }}</p>
      <button v-if="showRetry" class="btn-secondary mt-4" @click="$emit('retry')">Retry</button>
    </div>

    <div v-else-if="!rows.length" class="rounded-xl border border-dashed border-slate-200 bg-slate-50 px-4 py-8 text-center">
      <p class="text-[0.98rem] font-medium text-slate-900">{{ emptyTitle }}</p>
      <p class="mt-2 text-[0.96rem] text-slate-600">{{ emptyDescription }}</p>
    </div>

    <div v-else class="overflow-x-auto">
      <table class="min-w-full divide-y divide-slate-200">
        <thead class="sticky top-0 z-10 bg-white">
          <tr>
            <th v-for="column in columns" :key="column.key" class="px-3 py-3 text-left text-[0.78rem] font-medium uppercase tracking-[0.1em] text-slate-500 first:pl-0 last:pr-0">
              <button
                v-if="column.sortable"
                type="button"
                class="inline-flex items-center gap-2 transition hover:text-slate-900"
                @click="$emit('sort', column.key)"
              >
                <span>{{ column.label }}</span>
                <span class="text-[0.7rem]">{{ sortIndicator(column.key) }}</span>
              </button>
              <span v-else>{{ column.label }}</span>
            </th>
            <th v-if="$slots.actions" class="px-3 py-3 text-right text-[0.78rem] font-medium uppercase tracking-[0.1em] text-slate-500 first:pl-0 last:pr-0">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-200">
          <tr v-for="row in rows" :key="row.id || row.name" class="transition hover:bg-slate-50">
            <td v-for="column in columns" :key="column.key" class="px-3 py-4 align-top text-[0.97rem] text-slate-700 first:pl-0 last:pr-0">
              <slot :name="column.key" :row="row">
                {{ row[column.key] }}
              </slot>
            </td>
            <td v-if="$slots.actions" class="px-3 py-4 text-right align-top text-sm first:pl-0 last:pr-0">
              <slot name="actions" :row="row" />
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="$slots.footer" class="mt-4 border-t border-slate-200 pt-4">
      <slot name="footer" />
    </div>
  </section>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  title: string
  description?: string
  columns: Array<{ key: string; label: string; sortable?: boolean }>
  rows: any[]
  loading?: boolean
  error?: boolean
  errorTitle?: string
  errorDescription?: string
  showRetry?: boolean
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
  loadingTitle?: string
  loadingDescription?: string
  emptyTitle: string
  emptyDescription: string
  compact?: boolean
}>(), {
  loading: false,
  error: false,
  errorTitle: 'Table data could not be loaded.',
  errorDescription: 'Try the request again or adjust the current filters.',
  showRetry: true,
  sortBy: '',
  sortOrder: 'asc',
  loadingTitle: 'Loading',
  loadingDescription: 'Fetching table data.',
  compact: false,
})

defineEmits<{
  retry: []
  sort: [key: string]
}>()

function sortIndicator(key: string) {
  if (props.sortBy !== key) return '↕'
  return props.sortOrder === 'asc' ? '↑' : '↓'
}
</script>
