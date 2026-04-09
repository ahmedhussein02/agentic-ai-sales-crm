import { useState } from 'react'
import { CheckCircle, XCircle, Edit3 } from 'lucide-react'

interface Props {
  onAction: (action: 'approve' | 'reject' | 'edit', editedContent?: string) => Promise<void>
  submitting: boolean
}

export function HITLControls({ onAction, submitting }: Props) {
  const [mode, setMode] = useState<'idle' | 'editing'>('idle')
  const [editText, setEditText] = useState('')

  const handleEdit = async () => {
    if (editText.trim()) await onAction('edit', editText.trim())
  }

  return (
    <div className="card border-amber-400/30 bg-amber-400/5 space-y-4">
      <div className="flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
        <h3 className="font-semibold text-white text-sm">Human Review Required</h3>
        <span className="text-xs text-gray-500 ml-auto">
          Review the outputs above before approving
        </span>
      </div>

      {mode === 'idle' ? (
        <div className="flex gap-3">
          <button
            onClick={() => onAction('approve')}
            disabled={submitting}
            className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg
                       bg-success/20 hover:bg-success/30 border border-success/30
                       text-success font-semibold text-sm transition-colors disabled:opacity-40"
          >
            <CheckCircle size={16} />
            Approve & Send
          </button>

          <button
            onClick={() => setMode('editing')}
            disabled={submitting}
            className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg
                       bg-accent/20 hover:bg-accent/30 border border-accent/30
                       text-accent font-semibold text-sm transition-colors disabled:opacity-40"
          >
            <Edit3 size={16} />
            Edit & Approve
          </button>

          <button
            onClick={() => onAction('reject')}
            disabled={submitting}
            className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg
                       bg-danger/20 hover:bg-danger/30 border border-danger/30
                       text-danger font-semibold text-sm transition-colors disabled:opacity-40"
          >
            <XCircle size={16} />
            Reject
          </button>
        </div>
      ) : (
        <div className="space-y-3 animate-slide-up">
          <p className="text-xs text-gray-400">
            Edit the email content below, then submit your revised version:
          </p>
          <textarea
            value={editText}
            onChange={e => setEditText(e.target.value)}
            placeholder="Paste or type your edited email here…"
            rows={8}
            className="w-full bg-surface-700 border border-surface-600 rounded-lg p-3
                       text-sm text-gray-200 placeholder-gray-600 font-mono
                       focus:outline-none focus:border-accent resize-y"
          />
          <div className="flex gap-3">
            <button
              onClick={handleEdit}
              disabled={!editText.trim() || submitting}
              className="btn-primary flex-1"
            >
              {submitting ? 'Submitting…' : 'Submit Edit'}
            </button>
            <button
              onClick={() => setMode('idle')}
              disabled={submitting}
              className="btn-ghost"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  )
}