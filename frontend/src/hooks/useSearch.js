import { useQuery } from '@tanstack/react-query'
import { searchApi } from '../services/api.js'

export function useSearch(query, filters = {}, page = 0, limit = 20) {
  return useQuery({
    queryKey: ['search', query, filters, page, limit],
    queryFn: () =>
      searchApi.search({
        q: query,
        ...filters,
        limit,
        offset: page * limit,
      }),
    select: (res) => res.data,
    enabled: query.length > 0 || Object.keys(filters).length > 0,
  })
}

export function useSuggest(query, limit = 5) {
  return useQuery({
    queryKey: ['suggest', query, limit],
    queryFn: () => searchApi.suggest({ q: query, limit }),
    select: (res) => res.data,
    enabled: query.length >= 2,
  })
}
