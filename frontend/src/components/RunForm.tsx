import { useState } from 'react'
import { Search, Zap } from 'lucide-react'

const EXAMPLE_COMPANIES = [
  'NovaPay', 'HealthBridge AI', 'LogiStack',
  'Orbis Analytics', 'Zenova Security', 'Meridian Cloud',
]

interface Props {
  onSubmit: (companyName: string) => void
  loading: boolean
}

export function RunForm({ onSubmit, loading }: Props) {
  const [value, setValue] = useState('')

  const handleSubmit = () => {
    if (value.trim() && !loading) onSubmit(value.trim())
  }

  return (
    <div className="card space-y-4">
      <div className="flex items-center gap-2 mb-1">
        <Zap size={18} className="text-accent" />
        <h2 className="font-semibold text-white">New Analysis Run</h2>
      </div>

      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            type="text"
            value={value}
            onChange={e => setValue(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSubmit()}
            placeholder="Enter company name…"
            className="w-full bg-surface-700 border border-surface-600 rounded-lg
                       pl-9 pr-4 py-2.5 text-sm text-white placeholder-gray-500
                       focus:outline-none focus:border-accent transition-colors"
          />
        </div>
        <button
          onClick={handleSubmit}
          disabled={!value.trim() || loading}
          className="btn-primary flex items-center gap-2 whitespace-nowrap"
        >
          {loading ? (
            <>
              <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Running…
            </>
          ) : (
            'Run Analysis'
          )}
        </button>
      </div>

      {/* Quick-pick example companies */}
      <div className="flex flex-wrap gap-2">
        <span className="text-xs text-gray-500 self-center">Try:</span>
        {EXAMPLE_COMPANIES.map(name => (
          <button
            key={name}
            onClick={() => setValue(name)}
            className="text-xs px-2.5 py-1 rounded-full bg-surface-700 hover:bg-surface-600
                       text-gray-400 hover:text-white border border-surface-600
                       hover:border-accent transition-colors"
          >
            {name}
          </button>
        ))}
      </div>
    </div>
  )
}