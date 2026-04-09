import axios from 'axios'
import type { RunResult, RunSummary } from '@/types'

const http = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

export const api = {
  startRun: async (companyName: string): Promise<{ run_id: string; status: string }> => {
    const { data } = await http.post('/run-analysis', { company_name: companyName })
    return data
  },

  getResult: async (runId: string): Promise<RunResult> => {
    const { data } = await http.get(`/results/${runId}`)
    return data
  },

  submitHITL: async (
    runId: string,
    action: 'approve' | 'reject' | 'edit',
    editedContent?: string
  ): Promise<void> => {
    await http.post(`/hitl/${runId}`, { action, edited_content: editedContent ?? null })
  },

  listRuns: async (): Promise<RunSummary[]> => {
    const { data } = await http.get('/runs')
    return data
  },
}