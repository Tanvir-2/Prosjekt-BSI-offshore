import ResultCard from './ResultCard.jsx'

export default function ResultsList({ results, totalHits, query, loading, limit, offset, onPageChange }) {
  if (loading) {
    return (
      <div className="text-center py-12 text-gray-400">
        <div className="animate-spin inline-block w-6 h-6 border-2 border-bsi-blue border-t-transparent rounded-full mb-2" />
        <p className="text-sm">Searching...</p>
      </div>
    )
  }

  if (results.length === 0 && query) {
    return (
      <div className="text-center py-12 text-gray-400">
        <p className="text-lg">No results found</p>
        <p className="text-sm mt-1">Try a different search term or adjust your filters.</p>
      </div>
    )
  }

  if (results.length === 0) {
    return (
      <div className="text-center py-12 text-gray-400">
        <p className="text-lg">Start searching</p>
        <p className="text-sm mt-1">Type a filename in the search bar above.</p>
      </div>
    )
  }

  const currentPage = Math.floor(offset / limit)
  const totalPages = Math.ceil(totalHits / limit)

  return (
    <div>
      <p className="text-sm text-gray-500 mb-3">
        {totalHits} result{totalHits !== 1 ? 's' : ''} found
      </p>

      <div className="space-y-2">
        {results.map((result) => (
          <ResultCard key={result.id} result={result} />
        ))}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-6">
          <button
            onClick={() => onPageChange(currentPage - 1)}
            disabled={currentPage === 0}
            className="px-3 py-1.5 text-sm border border-gray-200 rounded bg-white hover:bg-gray-50 disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer"
          >
            Previous
          </button>
          <span className="text-sm text-gray-500">
            Page {currentPage + 1} of {totalPages}
          </span>
          <button
            onClick={() => onPageChange(currentPage + 1)}
            disabled={currentPage >= totalPages - 1}
            className="px-3 py-1.5 text-sm border border-gray-200 rounded bg-white hover:bg-gray-50 disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer"
          >
            Next
          </button>
        </div>
      )}
    </div>
  )
}
