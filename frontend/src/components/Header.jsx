import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth.js'
import bsiIcon from '../assets/bsi_offshore_icon.png'

const roleLabels = {
  admin: 'Admin',
  hr: 'HR',
  project_manager: 'Project Manager',
}

export default function Header() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <header className="bg-bsi-blue text-white shadow-md">
      <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <Link to="/" className="flex items-center gap-2 text-xl font-bold tracking-tight">
            <img src={bsiIcon} alt="BSI" className="h-[60px] w-[60px] object-contain" />
            BSI Search
          </Link>
          <nav className="flex gap-4 text-sm">
            <Link to="/" className="hover:text-bsi-green-light transition-colors">
              Search
            </Link>
            {user?.role === 'admin' && (
              <Link to="/admin" className="hover:text-bsi-green-light transition-colors">
                Admin
              </Link>
            )}
          </nav>
        </div>
        <div className="flex items-center gap-4 text-sm">
          <span className="opacity-80">{user?.full_name || user?.username}</span>
          <span className="bg-bsi-green/30 text-bsi-green-light px-2 py-0.5 rounded text-xs font-medium">
            {roleLabels[user?.role] || user?.role}
          </span>
          <button
            onClick={handleLogout}
            className="bg-white/10 hover:bg-white/20 px-3 py-1 rounded text-sm transition-colors cursor-pointer"
          >
            Logout
          </button>
        </div>
      </div>
    </header>
  )
}
