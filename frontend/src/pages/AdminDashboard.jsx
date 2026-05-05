import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { adminApi } from '../services/api.js'
import { useState } from 'react'

// ── Stats Cards ────────────────────────────────────────────

function StatsCards() {
  const { data, isLoading } = useQuery({
    queryKey: ['admin', 'stats'],
    queryFn: () => adminApi.getStats().then((r) => r.data),
  })

  if (isLoading) return <p className="text-gray-400 text-sm">Loading stats...</p>

  const topFileTypes = Object.entries(data?.by_file_type || {})
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div className="bg-white rounded-lg border border-gray-100 p-5 shadow-sm">
        <p className="text-xs font-medium text-gray-400 uppercase tracking-wide">Total Documents</p>
        <p className="text-3xl font-bold text-bsi-blue mt-1">{data?.total_documents ?? 0}</p>
      </div>
      <div className="bg-white rounded-lg border border-gray-100 p-5 shadow-sm">
        <p className="text-xs font-medium text-gray-400 uppercase tracking-wide">By Department</p>
        <div className="mt-2 space-y-1">
          {Object.entries(data?.by_department || {}).map(([dept, count]) => (
            <div key={dept} className="flex justify-between text-sm">
              <span className="text-gray-600">{dept}</span>
              <span className="font-medium text-gray-800">{count}</span>
            </div>
          ))}
          {Object.keys(data?.by_department || {}).length === 0 && (
            <p className="text-xs text-gray-400">No data</p>
          )}
        </div>
      </div>
      <div className="bg-white rounded-lg border border-gray-100 p-5 shadow-sm">
        <p className="text-xs font-medium text-gray-400 uppercase tracking-wide">Top File Types</p>
        <div className="mt-2 space-y-1">
          {topFileTypes.map(([type, count]) => (
            <div key={type} className="flex justify-between text-sm">
              <span className="text-gray-600">.{type}</span>
              <span className="font-medium text-gray-800">{count}</span>
            </div>
          ))}
          {topFileTypes.length === 0 && <p className="text-xs text-gray-400">No data</p>}
        </div>
      </div>
    </div>
  )
}



const roleLabels = { admin: 'Admin', hr: 'HR', project_manager: 'Project Manager' }
const roleColors = {
  admin: 'bg-purple-100 text-purple-700',
  hr: 'bg-blue-100 text-blue-700',
  project_manager: 'bg-green-100 text-green-700',
}

function UserTable() {
  const queryClient = useQueryClient()
  const [showModal, setShowModal] = useState(false)
  const [editUser, setEditUser] = useState(null)

  const { data: users = [], isLoading } = useQuery({
    queryKey: ['admin', 'users'],
    queryFn: () => adminApi.getUsers().then((r) => r.data),
  })

  const deactivateMutation = useMutation({
    mutationFn: (id) => adminApi.deactivateUser(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin', 'users'] }),
  })

  const activateMutation = useMutation({
    mutationFn: (id) => adminApi.activateUser(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin', 'users'] }),
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => adminApi.deleteUser(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin', 'users'] }),
  })

  const handleDeactivate = (user) => {
    if (confirm(`Deactivate user "${user.username}"? They will not be able to log in.`)) {
      deactivateMutation.mutate(user.id)
    }
  }

  const handleActivate = (user) => {
    if (confirm(`Activate user "${user.username}"? They will be able to log in again.`)) {
      activateMutation.mutate(user.id)
    }
  }

  const handleDelete = (user) => {
    if (confirm(`Permanently delete user "${user.username}"? This cannot be undone.`)) {
      deleteMutation.mutate(user.id)
    }
  }

  const handleEdit = (user) => {
    setEditUser(user)
    setShowModal(true)
  }

  const handleAdd = () => {
    setEditUser(null)
    setShowModal(true)
  }

  const handleModalClose = () => {
    setShowModal(false)
    setEditUser(null)
  }

  return (
    <div className="bg-white rounded-lg border border-gray-100 shadow-sm">
      <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
        <h2 className="text-base font-semibold text-gray-800">Users</h2>
        <button
          onClick={handleAdd}
          className="bg-bsi-green hover:bg-bsi-green-dark text-white text-xs font-medium px-3 py-1.5 rounded transition-colors cursor-pointer"
        >
          + Add User
        </button>
      </div>

      {isLoading ? (
        <p className="p-5 text-gray-400 text-sm">Loading users...</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs font-medium text-gray-400 uppercase tracking-wide border-b border-gray-100">
                <th className="px-5 py-3">Username</th>
                <th className="px-5 py-3">Full Name</th>
                <th className="px-5 py-3">Role</th>
                <th className="px-5 py-3">Status</th>
                <th className="px-5 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id} className="border-b border-gray-50 hover:bg-gray-50/50">
                  <td className="px-5 py-3 font-medium text-gray-800">{user.username}</td>
                  <td className="px-5 py-3 text-gray-500">{user.full_name || '—'}</td>
                  <td className="px-5 py-3">
                    <span className={`inline-block text-xs font-medium px-2 py-0.5 rounded ${roleColors[user.role] || 'bg-gray-100 text-gray-600'}`}>
                      {roleLabels[user.role] || user.role}
                    </span>
                  </td>
                  <td className="px-5 py-3">
                    {user.is_active ? (
                      <span className="inline-flex items-center gap-1 text-xs text-green-600">
                        <span className="w-1.5 h-1.5 bg-green-500 rounded-full" />
                        Active
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-xs text-gray-400">
                        <span className="w-1.5 h-1.5 bg-gray-300 rounded-full" />
                        Inactive
                      </span>
                    )}
                  </td>
                  <td className="px-5 py-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => handleEdit(user)}
                        className="text-xs text-bsi-blue hover:text-bsi-blue-dark cursor-pointer"
                      >
                        Edit
                      </button>
                      {user.is_active ? (
                        <button
                          onClick={() => handleDeactivate(user)}
                          className="text-xs text-orange-500 hover:text-orange-700 cursor-pointer"
                          disabled={deactivateMutation.isPending}
                        >
                          Deactivate
                        </button>
                      ) : (
                        <button
                          onClick={() => handleActivate(user)}
                          className="text-xs text-green-600 hover:text-green-800 cursor-pointer"
                          disabled={activateMutation.isPending}
                        >
                          Activate
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(user)}
                        className="text-xs text-red-500 hover:text-red-700 cursor-pointer"
                        disabled={deleteMutation.isPending}
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {users.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-5 py-8 text-center text-gray-400">
                    No users found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {showModal && (
        <UserModal user={editUser} onClose={handleModalClose} />
      )}
    </div>
  )
}



function UserModal({ user, onClose }) {
  const queryClient = useQueryClient()
  const isEdit = !!user

  const [form, setForm] = useState({
    username: user?.username || '',
    password: '',
    full_name: user?.full_name || '',
    role: user?.role || 'hr',
  })
  const [error, setError] = useState('')

  const saveMutation = useMutation({
    mutationFn: (data) => {
      if (isEdit) {
        return adminApi.updateUser(user.id, data)
      }
      return adminApi.createUser(data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] })
      onClose()
    },
    onError: (err) => {
      setError(err.response?.data?.detail || 'Operation failed')
    },
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    setError('')

    if (isEdit) {
      const update = { role: form.role }
      if (form.full_name) update.full_name = form.full_name
      saveMutation.mutate(update)
    } else {
      if (!form.username || !form.password) {
        setError('Username and password are required')
        return
      }
      const create = {
        username: form.username,
        password: form.password,
        role: form.role,
      }
      if (form.full_name) create.full_name = form.full_name
      saveMutation.mutate(create)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4" onClick={(e) => e.stopPropagation()}>
        <div className="px-5 py-4 border-b border-gray-100">
          <h3 className="text-base font-semibold text-gray-800">
            {isEdit ? 'Edit User' : 'Create New User'}
          </h3>
        </div>
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {!isEdit && (
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Username</label>
              <input
                type="text"
                value={form.username}
                onChange={(e) => setForm({ ...form, username: e.target.value })}
                className="w-full border border-gray-200 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-bsi-blue focus:border-transparent"
                placeholder="min 3 characters"
                disabled={isEdit}
              />
            </div>
          )}
          {!isEdit && (
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Password</label>
              <input
                type="password"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                className="w-full border border-gray-200 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-bsi-blue focus:border-transparent"
                placeholder="min 6 characters"
              />
            </div>
          )}
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Full Name</label>
            <input
              type="text"
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              className="w-full border border-gray-200 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-bsi-blue focus:border-transparent"
              placeholder="Optional"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Role</label>
            <select
              value={form.role}
              onChange={(e) => setForm({ ...form, role: e.target.value })}
              className="w-full border border-gray-200 rounded px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-bsi-blue focus:border-transparent"
            >
              <option value="hr">HR</option>
              <option value="project_manager">Project Manager</option>
              <option value="admin">Admin</option>
            </select>
          </div>

          {error && (
            <div className="bg-red-50 text-red-600 text-xs rounded px-3 py-2">{error}</div>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm text-gray-600 border border-gray-200 rounded hover:bg-gray-50 cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saveMutation.isPending}
              className="px-4 py-2 text-sm text-white bg-bsi-blue rounded hover:bg-bsi-blue-dark disabled:opacity-50 cursor-pointer"
            >
              {saveMutation.isPending ? 'Saving...' : isEdit ? 'Save Changes' : 'Create User'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}



function ConfigSection() {
  const queryClient = useQueryClient()
  const [newPath, setNewPath] = useState('')
  const [configError, setConfigError] = useState('')
  const [configSuccess, setConfigSuccess] = useState('')

  const { data: config, isLoading: configLoading } = useQuery({
    queryKey: ['admin', 'config'],
    queryFn: () => adminApi.getConfig().then((r) => r.data),
  })

  const reindexMutation = useMutation({
    mutationFn: () => adminApi.reindex(),
    onSuccess: (res) => {
      setConfigSuccess(res.data.message)
      queryClient.invalidateQueries({ queryKey: ['admin', 'stats'] })
    },
    onError: (err) => setConfigError(err.response?.data?.detail || 'Re-index failed'),
  })

  const configMutation = useMutation({
    mutationFn: (data_folder) => adminApi.updateConfig({ data_folder }),
    onSuccess: (res) => {
      setConfigSuccess(`Folder updated to: ${res.data.data_folder}`)
      setConfigError('')
      queryClient.invalidateQueries({ queryKey: ['admin', 'config'] })
      setNewPath('')
    },
    onError: (err) => {
      setConfigError(err.response?.data?.detail || 'Update failed')
      setConfigSuccess('')
    },
  })

  const handleSavePath = () => {
    setConfigError('')
    setConfigSuccess('')
    if (!newPath.trim()) return
    configMutation.mutate(newPath.trim())
  }

  const handleReindex = () => {
    setConfigError('')
    setConfigSuccess('')
    if (confirm('Re-index all files? This may take a moment for large folders.')) {
      reindexMutation.mutate()
    }
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {/* Data Folder Config */}
      <div className="bg-white rounded-lg border border-gray-100 p-5 shadow-sm">
        <h2 className="text-base font-semibold text-gray-800 mb-3">Data Folder</h2>
        {configLoading ? (
          <p className="text-gray-400 text-sm">Loading...</p>
        ) : (
          <>
            <p className="text-xs text-gray-400 mb-1">Current path</p>
            <p className="text-sm font-mono bg-gray-50 rounded px-3 py-2 mb-3 break-all text-gray-700">
              {config?.data_folder}
            </p>
            <div className="flex gap-2">
              <input
                type="text"
                value={newPath}
                onChange={(e) => setNewPath(e.target.value)}
                placeholder="Enter new folder path..."
                className="flex-1 border border-gray-200 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-bsi-blue focus:border-transparent"
              />
              <button
                onClick={handleSavePath}
                disabled={configMutation.isPending || !newPath.trim()}
                className="px-4 py-2 text-sm bg-bsi-blue text-white rounded hover:bg-bsi-blue-dark disabled:opacity-50 cursor-pointer whitespace-nowrap"
              >
                {configMutation.isPending ? 'Saving...' : 'Update'}
              </button>
            </div>
          </>
        )}
      </div>

      {/* Re-index */}
      <div className="bg-white rounded-lg border border-gray-100 p-5 shadow-sm">
        <h2 className="text-base font-semibold text-gray-800 mb-3">Index Management</h2>
        <p className="text-sm text-gray-500 mb-4">
          Trigger a full re-scan of the data folder. This rebuilds the search index from scratch with all current files.
        </p>
        <button
          onClick={handleReindex}
          disabled={reindexMutation.isPending}
          className="px-4 py-2 text-sm bg-bsi-green text-white rounded hover:bg-bsi-green-dark disabled:opacity-50 cursor-pointer"
        >
          {reindexMutation.isPending ? (
            <span className="inline-flex items-center gap-2">
              <span className="animate-spin inline-block w-3 h-3 border-2 border-white border-t-transparent rounded-full" />
              Re-indexing...
            </span>
          ) : (
            'Re-index All Files'
          )}
        </button>
      </div>

      {/* Status messages */}
      {configError && (
        <div className="md:col-span-2 bg-red-50 text-red-600 text-sm rounded-lg px-4 py-3">
          {configError}
        </div>
      )}
      {configSuccess && (
        <div className="md:col-span-2 bg-green-50 text-green-700 text-sm rounded-lg px-4 py-3">
          {configSuccess}
        </div>
      )}
    </div>
  )
}



export default function AdminDashboard() {
  return (
    <div className="max-w-5xl mx-auto px-4 py-6 space-y-6">
      <h1 className="text-2xl font-bold text-bsi-blue">Admin Dashboard</h1>

      {/* Stats */}
      <StatsCards />

      {/* User Management */}
      <UserTable />

      {/* Config & Reindex */}
      <ConfigSection />
    </div>
  )
}
