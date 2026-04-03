import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

type StringOption = {
  key: string
  defaultValue: string
}

type NumberOption = {
  key: string
  defaultValue: number
  min?: number
}

function readString(value: unknown, fallback: string) {
  if (typeof value !== 'string' || !value.trim()) return fallback
  return value
}

function readNumber(value: unknown, fallback: number, min = 0) {
  const parsed = Number(value)
  if (!Number.isFinite(parsed) || parsed < min) return fallback
  return parsed
}

export function useListQueryState(options: {
  pageSize: number
  search?: StringOption
  filters?: StringOption[]
  sortBy: StringOption
  sortOrder: StringOption
  page?: NumberOption
}) {
  const route = useRoute()
  const router = useRouter()

  const search = ref(options.search ? readString(route.query[options.search.key], options.search.defaultValue) : '')
  const filterRefs = Object.fromEntries(
    (options.filters || []).map((filter) => [filter.key, ref(readString(route.query[filter.key], filter.defaultValue))]),
  ) as Record<string, ReturnType<typeof ref<string>>>
  const sortBy = ref(readString(route.query[options.sortBy.key], options.sortBy.defaultValue))
  const sortOrder = ref(readString(route.query[options.sortOrder.key], options.sortOrder.defaultValue))
  const page = ref(readNumber(route.query[options.page?.key || 'page'], options.page?.defaultValue || 1, options.page?.min || 1))

  const offset = computed(() => Math.max(0, (page.value - 1) * options.pageSize))

  function updateQuery() {
    const nextQuery = { ...route.query }

    if (options.search) {
      if (search.value && search.value !== options.search.defaultValue) nextQuery[options.search.key] = search.value
      else delete nextQuery[options.search.key]
    }

    for (const filter of options.filters || []) {
      const value = filterRefs[filter.key].value
      if (value && value !== filter.defaultValue) nextQuery[filter.key] = value
      else delete nextQuery[filter.key]
    }

    if (sortBy.value !== options.sortBy.defaultValue) nextQuery[options.sortBy.key] = sortBy.value
    else delete nextQuery[options.sortBy.key]

    if (sortOrder.value !== options.sortOrder.defaultValue) nextQuery[options.sortOrder.key] = sortOrder.value
    else delete nextQuery[options.sortOrder.key]

    const pageKey = options.page?.key || 'page'
    if (page.value > 1) nextQuery[pageKey] = String(page.value)
    else delete nextQuery[pageKey]

    router.replace({ query: nextQuery })
  }

  watch([search, sortBy, sortOrder, ...Object.values(filterRefs)], () => {
    page.value = 1
    updateQuery()
  })

  watch(page, updateQuery)

  function setSort(key: string) {
    if (sortBy.value === key) {
      sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
      return
    }
    sortBy.value = key
    sortOrder.value = 'asc'
  }

  function setPage(nextPage: number) {
    page.value = Math.max(options.page?.min || 1, nextPage)
  }

  return {
    search,
    sortBy,
    sortOrder,
    page,
    offset,
    filters: filterRefs,
    setSort,
    setPage,
  }
}
