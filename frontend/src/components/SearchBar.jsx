import { useState, useEffect, useRef } from 'react'

export default function SearchBar({ onSearch }) {
  const [input, setInput] = useState('')
  const debounceRef = useRef(null)

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      onSearch(input)
    }, 300)
    return () => clearTimeout(debounceRef.current)
  }, [input, onSearch])

  return (
    <div className="relative">
      <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
        <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </div>
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Search files by name... (instant search)"
        className="w-full pl-12 pr-4 py-3 bg-white border border-gray-200 rounded-lg shadow-sm text-base focus:outline-none focus:ring-2 focus:ring-bsi-blue focus:border-transparent"
        autoFocus
      />
    </div>
  )
}
