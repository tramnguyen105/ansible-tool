import { onBeforeUnmount, ref, watch, type WatchSource } from 'vue'

type QueryResult<TItem, TMeta> = {
  items: TItem[]
  total: number
  has_more: boolean
} & TMeta

type UsePagedCollectionOptions<TItem, TMeta> = {
  pageSize?: number
  debounceMs?: number
  watchSources?: WatchSource[]
  query: (args: { limit: number; offset: number }) => Promise<QueryResult<TItem, TMeta>>
  onError?: (error: unknown) => void
}

export function usePagedCollection<TItem, TMeta extends Record<string, unknown> = Record<string, never>>(
  options: UsePagedCollectionOptions<TItem, TMeta>,
) {
  const pageSize = options.pageSize ?? 10
  const debounceMs = options.debounceMs ?? 250

  const items = ref<TItem[]>([])
  const isLoading = ref(true)
  const total = ref(0)
  const hasMore = ref(false)
  const offset = ref(0)
  const meta = ref({} as TMeta)
  let filterTimer: ReturnType<typeof setTimeout> | null = null

  async function load() {
    isLoading.value = true
    try {
      const response = await options.query({ limit: pageSize, offset: offset.value })
      items.value = response.items
      total.value = response.total
      hasMore.value = response.has_more
      meta.value = { ...response } as TMeta
    } catch (error) {
      options.onError?.(error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  function refreshFromStart() {
    offset.value = 0
    return load()
  }

  function nextPage() {
    if (!hasMore.value) return
    offset.value += pageSize
    return load()
  }

  function previousPage() {
    if (offset.value === 0) return
    offset.value = Math.max(0, offset.value - pageSize)
    return load()
  }

  if (options.watchSources?.length) {
    watch(options.watchSources, () => {
      if (filterTimer) clearTimeout(filterTimer)
      filterTimer = setTimeout(() => {
        refreshFromStart().catch(() => undefined)
      }, debounceMs)
    })
  }

  onBeforeUnmount(() => {
    if (filterTimer) clearTimeout(filterTimer)
  })

  return {
    items,
    isLoading,
    total,
    hasMore,
    offset,
    pageSize,
    meta,
    load,
    refreshFromStart,
    nextPage,
    previousPage,
  }
}
