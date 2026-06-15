import React, { useEffect, useMemo, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { Clapperboard, ImageUp, Play, Sparkles, Wand2, AlertCircle } from 'lucide-react'
import './styles.css'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

// Error boundary for catching React errors
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    console.error('App error:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <main className="min-h-screen bg-[#ece7dd] text-ink flex items-center justify-center">
          <div className="max-w-md text-center">
            <AlertCircle className="mx-auto mb-4 h-12 w-12 text-red-600" />
            <h1 className="text-xl font-semibold mb-2">Application Error</h1>
            <p className="text-black/60 mb-4">{this.state.error?.message}</p>
            <button onClick={() => window.location.reload()} className="bg-ink text-white px-4 py-2 rounded hover:bg-black">
              Reload App
            </button>
          </div>
        </main>
      )
    }
    return this.props.children
  }
}

const templates = [
  ['cinematic_male', 'Cinematic Male'],
  ['kitchen_scene', 'Kitchen Scene'],
  ['luxury_scene', 'Luxury Scene']
]

function absoluteOutput(path) {
  if (!path) return ''
  const normalized = path.replaceAll('\\', '/')
  const marker = '/outputs/'
  const index = normalized.indexOf(marker)
  return index >= 0 ? `${API_BASE}${normalized.slice(index)}` : path
}

async function api(path, body) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  })
  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`API error: ${errorText}`)
  }
  return response.json()
}

function App() {
  const [prompt, setPrompt] = useState('Ultra realistic Indian businessman in luxury office')
  const [template, setTemplate] = useState('cinematic_male')
  const [model, setModel] = useState('auto')
  const [seed, setSeed] = useState('')
  const [width, setWidth] = useState(512)
  const [height, setHeight] = useState(768)
  const [steps, setSteps] = useState(16)
  const [jobs, setJobs] = useState([])
  const [activeImage, setActiveImage] = useState('')
  const [error, setError] = useState('')
  const latest = useMemo(() => jobs.find((job) => job.status === 'completed' && job.result?.image_path), [jobs])

  useEffect(() => {
    const timer = setInterval(async () => {
      setJobs((current) => {
        const active = current.filter((job) => ['queued', 'running'].includes(job.status))
        if (active.length > 0) {
          active.forEach(async (job) => {
            try {
              const response = await fetch(`${API_BASE}/jobs/${job.id}`)
              if (!response.ok) {
                console.error(`Failed to fetch job ${job.id}: ${response.status}`)
                return
              }
              const updated = await response.json()
              setJobs((items) => items.map((item) => (item.id === updated.id ? updated : item)))
              if (updated.result?.image_path) setActiveImage(updated.result.image_path)
            } catch (err) {
              console.error(`Polling error for job ${job.id}:`, err)
            }
          })
        }
        return current
      })
    }, 1200)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    if (latest?.result?.image_path && !activeImage) setActiveImage(latest.result.image_path)
  }, [latest, activeImage])

  const submitImage = async () => {
    try {
      setError('')
      if (!prompt.trim()) {
        setError('Please enter a prompt')
        return
      }
      const job = await api('/generate-image', {
        prompt,
        template,
        model,
        width: Number(width) || 512,
        height: Number(height) || 768,
        steps: Number(steps) || 16,
        guidance_scale: 4.0,
        seed: seed ? Number(seed) : null
      })
      setJobs((items) => [{ ...job, type: 'generate-image', progress: 0 }, ...items])
    } catch (err) {
      setError(`Generation failed: ${err.message}`)
      console.error('Generate error:', err)
    }
  }

  const enhance = async () => {
    try {
      if (!activeImage) return
      const job = await api('/enhance-image', { image_path: activeImage, upscale: 2, face_enhancer: 'gfpgan' })
      setJobs((items) => [{ ...job, type: 'enhance-image', progress: 0 }, ...items])
    } catch (err) {
      setError(`Enhancement failed: ${err.message}`)
      console.error('Enhance error:', err)
    }
  }

  const video = async () => {
    try {
      if (!activeImage) return
      const job = await api('/generate-video', { image_path: activeImage, seconds: 5, fps: 24 })
      setJobs((items) => [{ ...job, type: 'generate-video', progress: 0 }, ...items])
    } catch (err) {
      setError(`Video generation failed: ${err.message}`)
      console.error('Video error:', err)
    }
  }

  return (
    <main className="min-h-screen bg-[#ece7dd] text-ink">
      <header className="border-b border-black/10 bg-[#fbfaf7]">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4">
          <div className="flex items-center gap-3">
            <Clapperboard className="h-7 w-7 text-teal" />
            <div>
              <h1 className="text-xl font-semibold tracking-normal">CineHuman AI Studio</h1>
              <p className="text-sm text-black/55">Photorealistic image, enhancement, and motion pipeline</p>
            </div>
          </div>
          <span className="rounded-sm border border-teal/30 bg-teal/10 px-3 py-1 text-sm text-teal">Local FOSS stack</span>
        </div>
      </header>

      <section className="mx-auto grid max-w-7xl gap-5 px-5 py-5 lg:grid-cols-[390px_1fr]">
        <aside className="space-y-4">
          <div className="rounded-md border border-black/10 bg-[#fbfaf7] p-4 shadow-sm">
            <label className="text-sm font-medium">Prompt</label>
            <textarea
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              className="mt-2 h-28 w-full resize-none rounded border border-black/15 bg-white p-3 text-sm outline-none focus:border-teal"
              placeholder="Describe the image you want to generate..."
            />
            <div className="mt-3 grid grid-cols-2 gap-3">
              <select value={template} onChange={(event) => setTemplate(event.target.value)} className="control">
                {templates.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
              </select>
              <select value={model} onChange={(event) => setModel(event.target.value)} className="control">
                {['auto', 'sd15_tiny', 'sd15', 'sdxl', 'juggernaut', 'realvis', 'dreamshaper'].map((value) => <option key={value}>{value}</option>)}
              </select>
              <input className="control" type="number" placeholder="Width" value={width} onChange={(event) => setWidth(event.target.value)} />
              <input className="control" type="number" placeholder="Height" value={height} onChange={(event) => setHeight(event.target.value)} />
              <input className="control" type="number" placeholder="Steps" value={steps} onChange={(event) => setSteps(event.target.value)} />
              <input className="control" type="number" placeholder="Seed (optional)" value={seed} onChange={(event) => setSeed(event.target.value)} />
            </div>
            <button onClick={submitImage} className="mt-4 flex w-full items-center justify-center gap-2 rounded bg-ink px-4 py-3 text-sm font-medium text-white hover:bg-black transition-colors">
              <Wand2 className="h-4 w-4" /> Generate Image
            </button>
          </div>

          <div className="rounded-md border border-black/10 bg-[#fbfaf7] p-4 shadow-sm">
            <div className="grid grid-cols-2 gap-3">
              <button onClick={enhance} className="action" disabled={!activeImage}><Sparkles className="h-4 w-4" /> Enhance</button>
              <button onClick={video} className="action" disabled={!activeImage}><Play className="h-4 w-4" /> Video</button>
            </div>
            {error && <p className="mt-3 rounded bg-red-50 p-2 text-sm text-red-700">{error}</p>}
          </div>
        </aside>

        <section className="grid gap-5 xl:grid-cols-[1fr_360px]">
          <div className="flex min-h-[680px] items-center justify-center rounded-md border border-black/10 bg-[#111316] p-4">
            {activeImage ? (
              <img src={absoluteOutput(activeImage)} alt="Generated" className="max-h-[78vh] rounded-sm object-contain shadow-2xl" />
            ) : (
              <div className="text-center text-white/65">
                <ImageUp className="mx-auto mb-3 h-10 w-10" />
                <p>Generated portraits appear here.</p>
              </div>
            )}
          </div>

          <div className="rounded-md border border-black/10 bg-[#fbfaf7] p-4 shadow-sm">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-black/55">Jobs</h2>
            <div className="space-y-3">
              {jobs.map((job) => (
                <div key={job.id} className="rounded border border-black/10 bg-white p-3">
                  <div className="flex items-center justify-between gap-2 text-sm">
                    <span className="font-medium">{job.type}</span>
                    <span className={`text-xs font-semibold ${job.status === 'completed' ? 'text-green-600' : job.status === 'failed' ? 'text-red-600' : 'text-blue-600'}`}>{job.status}</span>
                  </div>
                  <div className="mt-2 h-2 rounded bg-black/10 overflow-hidden">
                    <div className="h-2 rounded bg-teal transition-all" style={{ width: `${Math.round((job.progress || 0) * 100)}%` }} />
                  </div>
                  {job.result?.video_path && <a className="mt-2 block text-sm text-teal hover:underline" href={absoluteOutput(job.result.video_path)} target="_blank" rel="noopener noreferrer">Download MP4</a>}
                  {job.result?.fallback && <p className="mt-2 text-xs text-amber-700">{job.result.fallback_reason}</p>}
                  {job.error && <p className="mt-2 text-xs text-red-700">{job.error}</p>}
                </div>
              ))}
            </div>
          </div>
        </section>
      </section>
    </main>
  )
}

createRoot(document.getElementById('root')).render(
  <ErrorBoundary>
    <App />
  </ErrorBoundary>
)
