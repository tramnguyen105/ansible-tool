<template>
  <section class="rounded-2xl border border-slate-800 bg-slate-900 p-5">
    <div class="mb-4 flex items-start justify-between gap-3">
      <div>
        <h3 class="text-[1.15rem] font-semibold text-white">{{ title }}</h3>
        <p v-if="description" class="mt-1 text-[0.96rem] text-slate-400">{{ description }}</p>
      </div>
      <slot name="actions" />
    </div>

    <div v-if="!rows.length" class="rounded-xl border border-dashed border-slate-800 bg-slate-950/70 px-4 py-8 text-center">
      <p class="text-[0.98rem] font-medium text-white">{{ emptyTitle }}</p>
      <p class="mt-2 text-[0.96rem] text-slate-400">{{ emptyDescription }}</p>
    </div>

    <div v-else class="overflow-x-auto">
      <table class="min-w-full divide-y divide-slate-800">
        <thead>
          <tr>
            <th v-for="column in columns" :key="column.key" class="px-3 py-3 text-left text-[0.78rem] font-medium uppercase tracking-[0.1em] text-slate-500 first:pl-0 last:pr-0">
              {{ column.label }}
            </th>
            <th v-if="$slots.actions" class="px-3 py-3 text-right text-[0.78rem] font-medium uppercase tracking-[0.1em] text-slate-500 first:pl-0 last:pr-0">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-800">
          <tr v-for="row in rows" :key="row.id || row.name" class="transition hover:bg-slate-950/60">
            <td v-for="column in columns" :key="column.key" class="px-3 py-4 align-top text-[0.97rem] text-slate-300 first:pl-0 last:pr-0">
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
  </section>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  description?: string
  columns: Array<{ key: string; label: string }>
  rows: any[]
  emptyTitle: string
  emptyDescription: string
  compact?: boolean
}>()
</script>
