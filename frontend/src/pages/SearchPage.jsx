import { useState, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { searchApi } from '../services/api.js'
import { useAuth } from '../hooks/useAuth.js'
import SearchBar from '../components/SearchBar.jsx'
import FilterPanel from '../components/FilterPanel.jsx'
import ResultsList from '../components/ResultsList.jsx'

export default function SearchPage() {
  const { user } = useAuth()
  const [query, setQuery] = useState('')
  const [filters, setFilters] = useState({})
  const [page, setPage] = useState(0)
  const limit = 20

  const { data, isLoading, error } = useQuery({
    queryKey: ['search', query, filters, page],
    queryFn: () =>
      searchApi.search({
        q: query,
        ...filters,
        limit,
        offset: page * limit,
      }),
    select: (res) => res.data,
  })

  const handleSearch = useCallback((q) => {
    setQuery(q)
    setPage(0)
  }, [])

  const handleFilterChange = useCallback((newFilters) => {
    setFilters(newFilters)
    setPage(0)
  }, [])

  return (
    <div className="max-w-5xl mx-auto px-4 py-6">
      <SearchBar onSearch={handleSearch} />

      <div className="mt-4 flex gap-6">
        <aside className="w-56 shrink-0">
          <FilterPanel filters={filters} onChange={handleFilterChange} />
        </aside>
        <main className="flex-1 min-w-0">
          {error && (
            <div className="bg-red-50 text-red-600 rounded px-4 py-3 text-sm mb-4">
              {error.response?.data?.detail || 'Search failed'}
            </div>
          )}
          <ResultsList
            results={data?.results || []}
            totalHits={data?.total_hits || 0}
            query={query}
            loading={isLoading}
            limit={limit}
            offset={page * limit}
            onPageChange={setPage}
          />
        </main>
      </div>
    </div>
  )
}
