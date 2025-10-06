import React, { useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { useChatStore } from './store'

const apiBase = '/api'

export default function App() {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { messages, addMessage, loading, setLoading, clear } = useChatStore()
  const [question, setQuestion] = useState('')
  const [ingestInfo, setIngestInfo] = useState<string>('')
  const [provider, setProvider] = useState<'auto' | 'openai' | 'ollama'>('auto')

  async function uploadFiles(files: FileList) {
    const form = new FormData()
    Array.from(files).forEach((f) => form.append('files', f))
    setIngestInfo('Uploading...')
    try {
      const res = await fetch(`${apiBase}/upload`, { method: 'POST', body: form })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      const { files_ingested, files_skipped, chunks_added } = data
      setIngestInfo(
        `Ingested: ${files_ingested?.length || 0}, Skipped: ${files_skipped?.length || 0}, Chunks: ${chunks_added}`
      )
    } catch (e: any) {
      setIngestInfo('Upload failed: ' + e.message)
    }
  }

  async function ask() {
    const q = question.trim()
    if (!q) return
    addMessage({ id: crypto.randomUUID(), role: 'user', content: q })
    setQuestion('')
    setLoading(true)
    try {
      const res = await fetch(`${apiBase}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q, provider }),
      })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      const md = formatAnswer(data)
      addMessage({ id: crypto.randomUUID(), role: 'assistant', content: md })
    } catch (e: any) {
      addMessage({ id: crypto.randomUUID(), role: 'assistant', content: 'Error: ' + e.message })
    } finally {
      setLoading(false)
    }
  }

  function formatAnswer(data: any) {
    const sources = (data?.sources || []) as { source: string; page?: number }[]
    const srcMd = sources
      .map((s: any) => `- ${s.source}${s.page != null ? ` (p. ${s.page})` : ''}`)
      .join('\n')
    const base = data?.answer || ''
    return srcMd ? `${base}\n\n### Sources\n${srcMd}` : base
  }

  return (
    <div className="container">
      <div className="header">
        <h2>AI Copilot for Engineers</h2>
        <div className="badge">Local RAG</div>
      </div>

      <div className="panel" style={{ marginBottom: 16 }}>
        <div className="row" style={{ alignItems: 'center' }}>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            onChange={(e) => e.target.files && uploadFiles(e.target.files)}
          />
          <button onClick={() => fileInputRef.current?.click()}>Upload</button>
          <button onClick={clear}>Clear Chat</button>
          <select value={provider} onChange={(e) => setProvider(e.target.value as any)}>
            <option value="auto">Auto</option>
            <option value="openai">OpenAI</option>
            <option value="ollama">Ollama</option>
          </select>
        </div>
        <div style={{ marginTop: 8, color: '#9ca3af' }}>{ingestInfo}</div>
      </div>

      <div className="panel chat" style={{ height: 420, overflow: 'auto', marginBottom: 16 }}>
        {messages.map((m) => (
          <div key={m.id} className={`msg ${m.role}`}>
            <ReactMarkdown>{m.content}</ReactMarkdown>
          </div>
        ))}
      </div>

      <div className="panel">
        <div className="row">
          <input
            placeholder="Ask engineering question... e.g., Q=2 L/s v=1 m/s"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') ask()
            }}
          />
          <button disabled={loading} onClick={ask}>
            {loading ? 'Thinking…' : 'Ask'}
          </button>
        </div>
      </div>
    </div>
  )
}
