'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { clsx } from 'clsx'
import { Dumbbell, History, ListChecks, LayoutDashboard, LogOut } from 'lucide-react'

const nav = [
  { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { label: 'Schede', href: '/dashboard/workouts', icon: Dumbbell },
  { label: 'Esercizi', href: '/dashboard/exercises', icon: ListChecks },
  { label: 'Storico', href: '/dashboard/history', icon: History },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="flex w-64 flex-col border-r border-gray-200 bg-white">
      <div className="px-6 py-5">
        <span className="text-xl font-bold text-brand-700">MyFit Journal</span>
      </div>
      <nav className="flex-1 space-y-1 px-3">
        {nav.map(({ label, href, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={clsx(
              'flex items-center gap-3 rounded-lg px-4 py-2.5 text-sm font-medium transition-colors',
              pathname === href
                ? 'bg-brand-50 text-brand-700'
                : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900',
            )}
          >
            <Icon size={18} />
            {label}
          </Link>
        ))}
      </nav>
      <div className="border-t border-gray-200 px-3 py-4">
        <button
          onClick={() => {
            localStorage.removeItem('token')
            window.location.href = '/login'
          }}
          className="flex w-full items-center gap-3 rounded-lg px-4 py-2.5 text-sm font-medium text-gray-600 hover:bg-gray-100"
        >
          <LogOut size={18} />
          Esci
        </button>
      </div>
    </aside>
  )
}
