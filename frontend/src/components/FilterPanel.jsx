const departments = ['', 'Prosjekt', 'HR', 'Driftsmøter']
const fileTypes = ['', 'pdf', 'docx', 'xlsx', 'xls', 'pptx', 'msg', 'jpg', 'heic', 'doc', 'mov', 'zip']

export default function FilterPanel({ filters, onChange }) {
  const handleChange = (key, value) => {
    onChange({ ...filters, [key]: value || undefined })
  }

  const handleClear = () => {
    onChange({})
  }

  const hasFilters = filters.department || filters.file_type || filters.date_from || filters.date_to

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-700">Filters</h3>
        {hasFilters && (
          <button
            onClick={handleClear}
            className="text-xs text-bsi-blue hover:text-bsi-blue-dark cursor-pointer"
          >
            Clear all
          </button>
        )}
      </div>

      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1">Department</label>
        <select
          value={filters.department || ''}
          onChange={(e) => handleChange('department', e.target.value)}
          className="w-full border border-gray-200 rounded px-2 py-1.5 text-sm bg-white focus:outline-none focus:ring-1 focus:ring-bsi-blue"
        >
          <option value="">All departments</option>
          {departments.filter(Boolean).map((d) => (
            <option key={d} value={d}>{d}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1">File type</label>
        <select
          value={filters.file_type || ''}
          onChange={(e) => handleChange('file_type', e.target.value)}
          className="w-full border border-gray-200 rounded px-2 py-1.5 text-sm bg-white focus:outline-none focus:ring-1 focus:ring-bsi-blue"
        >
          <option value="">All types</option>
          {fileTypes.filter(Boolean).map((t) => (
            <option key={t} value={t}>.{t}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1">Date from</label>
        <input
          type="date"
          value={filters.date_from || ''}
          onChange={(e) => handleChange('date_from', e.target.value)}
          className="w-full border border-gray-200 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-bsi-blue"
        />
      </div>

      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1">Date to</label>
        <input
          type="date"
          value={filters.date_to || ''}
          onChange={(e) => handleChange('date_to', e.target.value)}
          className="w-full border border-gray-200 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-bsi-blue"
        />
      </div>
    </div>
  )
}
