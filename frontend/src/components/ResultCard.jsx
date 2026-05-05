import { docsApi } from '../services/api.js'

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function HighlightedName({ highlight }) {
  if (!highlight || !highlight.includes('<em>')) {
    return <span>{highlight || ''}</span>
  }
  
  const parts = highlight.split(/(<em>.*?<\/em>)/g)
  return (
    <span>
      {parts.map((part, i) => {
        if (part.startsWith('<em>') && part.endsWith('</em>')) {
          return <mark key={i} className="bg-yellow-200 text-inherit rounded px-0.5">{part.slice(4, -5)}</mark>
        }
        return <span key={i}>{part}</span>
      })}
    </span>
  )
}

export default function ResultCard({ result }) {
  const handlePreview = () => {
    window.open(docsApi.previewUrl(result.id), '_blank')
  }

  const handleDownload = () => {
    const link = document.createElement('a')
    link.href = docsApi.downloadUrl(result.id)
    link.download = result.file_name
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  return (
    <div className="bg-white border border-gray-100 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <h3 className="text-sm font-semibold text-bsi-blue truncate">
            <HighlightedName highlight={result.highlight} />
          </h3>
          <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
            <span className="bg-gray-100 px-2 py-0.5 rounded">{result.department}</span>
            <span className="uppercase">{result.file_type}</span>
            <span>{formatSize(result.file_size)}</span>
            <span>Created: {result.created_at}</span>
          </div>
        </div>
        <div className="flex gap-1.5 shrink-0">
          <button
            onClick={handlePreview}
            className="px-3 py-1 text-xs bg-bsi-blue text-white rounded hover:bg-bsi-blue-dark transition-colors cursor-pointer"
          >
            Preview
          </button>
          <button
            onClick={handleDownload}
            className="px-3 py-1 text-xs border border-gray-200 text-gray-600 rounded hover:bg-gray-50 transition-colors cursor-pointer"
          >
            Download
          </button>
        </div>
      </div>
    </div>
  )
}
