import { useEffect, useMemo, useState } from 'react'
import {
  ShieldCheck, LayoutDashboard, Plus, BrainCircuit, Database, MessageSquare,
  FileText, Settings, Search, Bell, ArrowRight, UploadCloud, CheckCircle2,
  AlertCircle, FileArchive, X, LoaderCircle, Activity
} from 'lucide-react'
import { api } from './api'

type Assessment = {
  id: number; company_name: string; model_name: string; model_type: string;
  intended_use: string; deployment_context: string; status: string;
  created_at: string; uploads: { id: number; upload_kind: string; original_filename: string;
    size_bytes: number; inspection: Record<string, unknown> }[];
  findings?: { id: number; framework: string; function: string; category: string; title: string; status: string; severity: string; evidence: string; rationale: string; source_type: string }[]
}
type FormState = {
  company_name: string; model_name: string; model_type: string;
  intended_use: string; deployment_context: string
}
const initialForm: FormState = {
  company_name: '', model_name: '', model_type: 'Machine Learning',
  intended_use: '', deployment_context: ''
}

export default function App() {
  const [items, setItems] = useState<Assessment[]>([])
  const [selected, setSelected] = useState<Assessment | null>(null)
  const [page, setPage] = useState<'dashboard'|'new'|'detail'>('dashboard')
  const [form, setForm] = useState(initialForm)
  const [modelFile, setModelFile] = useState<File | null>(null)
  const [datasets, setDatasets] = useState<Record<string, File | null>>({training:null, validation:null, test:null})
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [apiOnline, setApiOnline] = useState(false)

  async function refresh() {
    try { setItems(await api.listAssessments()); setApiOnline(true) }
    catch { setApiOnline(false) }
  }
  useEffect(() => { refresh() }, [])
  const totalUploads = useMemo(() => items.reduce((n, a) => n + a.uploads.length, 0), [items])

  function update<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm(old => ({...old, [key]: value}))
  }

  async function create() {
    setError(''); setNotice('')
    if (!form.company_name.trim() || !form.model_name.trim() || !form.intended_use.trim()) {
      setError('Please complete company name, model name and intended use.'); return
    }
    if (!modelFile) { setError('Please upload the model ZIP file.'); return }
    if (modelFile.size > 100 * 1024 * 1024) { setError('Model ZIP must be 100 MB or smaller.'); return }
    setBusy(true)
    try {
      const created = await api.createAssessment(form) as Assessment
      await api.uploadModel(created.id, modelFile)
      for (const kind of ['training','validation','test']) {
        const file = datasets[kind]
        if (file) await api.uploadDataset(created.id, kind, file)
      }
      const refreshed = await api.listAssessments() as Assessment[]
      setItems(refreshed)
      const latest = refreshed.find(a => a.id === created.id) || created
      setSelected(latest); setPage('detail')
      setNotice('Assessment created and files uploaded successfully.')
      setForm(initialForm); setModelFile(null)
      setDatasets({training:null, validation:null, test:null})
    } catch (e) { setError(e instanceof Error ? e.message : 'Something went wrong.') }
    finally { setBusy(false) }
  }

  async function runAssessment() {
    if (!selected) return
    setBusy(true); setError(''); setNotice('')
    try {
      const updated = await api.runAssessment(selected.id) as Assessment
      setSelected(updated)
      setNotice('Preliminary assessment completed. Review the findings below.')
      await refresh()
    } catch (e) { setError(e instanceof Error ? e.message : 'Assessment could not be run.') }
    finally { setBusy(false) }
  }

  async function openAssessment(item: Assessment) {
    try { const latest = await fetch(`${import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'}/api/assessments/${item.id}`).then(r => r.json()); setSelected(latest) }
    catch { setSelected(item) }
    setPage('detail')
  }

  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark"><ShieldCheck size={22}/></div><div><b>AI GRC</b><small>ASSESSMENT WORKSPACE</small></div></div>
      <div className="nav-label">WORKSPACE</div>
      <button className={`nav-item ${page==='dashboard'?'active':''}`} onClick={()=>setPage('dashboard')}><LayoutDashboard size={18}/> Dashboard</button>
      <button className={`nav-item ${page==='new'?'active':''}`} onClick={()=>{setPage('new');setError('')}}><Plus size={18}/> New assessment</button>
      <div className="nav-label spaced">ASSESSMENT</div>
      <button className="nav-item muted" onClick={()=>setNotice('Model analysis will be enabled after the NIST assessment module is added.')}><BrainCircuit size={18}/> Model analysis</button>
      <button className="nav-item muted" onClick={()=>setNotice('Dataset analysis is the next development module.')}><Database size={18}/> Datasets</button>
      <button className="nav-item muted" onClick={()=>setNotice('The interactive GRC agent is coming in the next phase.')}><MessageSquare size={18}/> GRC agent</button>
      <button className="nav-item muted" onClick={()=>setNotice('Assessment reports will appear here once NIST evaluation is implemented.')}><FileText size={18}/> Reports</button>
      <div className="sidebar-bottom"><div className={`connection ${apiOnline?'online':'offline'}`}><span/> API {apiOnline?'connected':'not connected'}</div><div className="user-chip"><div className="avatar">G</div><div><b>Assessment user</b><small>Prototype workspace</small></div><Settings size={16}/></div></div>
    </aside>

    <main className="main">
      <header className="topbar"><div className="crumb">Workspace <span>/</span> {page==='new'?'New assessment':page==='detail'?'Assessment details':'Dashboard'}</div><div className="top-actions"><div className="search"><Search size={15}/><span>Search assessments</span><kbd>⌘ K</kbd></div><button className="icon-btn" aria-label="Notifications"><Bell size={18}/></button><div className="avatar small">G</div></div></header>
      <div className="content">
        {notice && <div className="notice"><CheckCircle2 size={16}/>{notice}<button onClick={()=>setNotice('')}><X size={15}/></button></div>}
        {error && <div className="error"><AlertCircle size={16}/>{error}<button onClick={()=>setError('')}><X size={15}/></button></div>}

        {page==='dashboard' && <section>
          <div className="page-heading"><div><div className="eyebrow">OVERVIEW</div><h1>Assessment dashboard</h1><p>Manage AI model governance and risk assessments.</p></div><button className="primary" onClick={()=>{setPage('new');setError('')}}><Plus size={17}/> New assessment</button></div>
          <div className="stats-grid">
            <div className="stat-card"><div className="stat-top"><span>Total assessments</span><LayoutDashboard size={17}/></div><strong>{items.length.toString().padStart(2,'0')}</strong><small>Created in this workspace</small></div>
            <div className="stat-card"><div className="stat-top"><span>Files received</span><Database size={17}/></div><strong>{totalUploads.toString().padStart(2,'0')}</strong><small>Model and dataset uploads</small></div>
            <div className="stat-card"><div className="stat-top"><span>Framework</span><ShieldCheck size={17}/></div><strong className="framework-stat">NIST AI RMF</strong><small>Assessment framework</small></div>
          </div>
          <div className="section-heading"><div><h2>Recent assessments</h2><p>Your latest model submissions</p></div><span className="count-pill">{items.length} total</span></div>
          <div className="table-card">
            {items.length===0 ? <div className="empty"><div className="empty-icon"><FileText size={25}/></div><h3>No assessments yet</h3><p>Create your first assessment to get started.</p><button className="secondary" onClick={()=>setPage('new')}><Plus size={16}/> Create assessment</button></div> :
            <table><thead><tr><th>MODEL / COMPANY</th><th>MODEL TYPE</th><th>STATUS</th><th>CREATED</th><th></th></tr></thead><tbody>{items.map(item=><tr key={item.id} onClick={()=>openAssessment(item)}><td><b>{item.model_name}</b><small>{item.company_name}</small></td><td>{item.model_type}</td><td><span className="status"><span/>{item.status}</span></td><td>{new Date(item.created_at).toLocaleDateString()}</td><td><ArrowRight size={16}/></td></tr>)}</tbody></table>}
          </div>
        </section>}

        {page==='new' && <section>
          <div className="page-heading"><div><div className="eyebrow">NEW SUBMISSION</div><h1>Create an assessment</h1><p>Provide model details and upload the model package to begin.</p></div><button className="text-button" onClick={()=>setPage('dashboard')}>Cancel</button></div>
          <div className="form-layout">
            <div className="form-main">
              <div className="panel"><div className="panel-title"><div className="step-icon">01</div><div><h2>Company and model information</h2><p>Basic information about the organization and AI system.</p></div></div>
                <div className="form-grid">
                  <label>Company name <input value={form.company_name} onChange={e=>update('company_name',e.target.value)} placeholder="e.g. Acme Technologies"/></label>
                  <label>Model name <input value={form.model_name} onChange={e=>update('model_name',e.target.value)} placeholder="e.g. Customer Risk Predictor"/></label>
                  <label>Model type <select value={form.model_type} onChange={e=>update('model_type',e.target.value)}><option>Machine Learning</option><option>Deep Learning</option><option>Large Language Model</option><option>Computer Vision</option><option>Natural Language Processing</option><option>Other</option></select></label>
                  <label className="full">Intended use <textarea value={form.intended_use} onChange={e=>update('intended_use',e.target.value)} placeholder="Describe what the model does, who uses it and what decisions it supports."/></label>
                  <label className="full">Deployment context <textarea value={form.deployment_context} onChange={e=>update('deployment_context',e.target.value)} placeholder="Where will the model run? Who will be affected by its outputs? (Optional)"/></label>
                </div>
              </div>
              <div className="panel"><div className="panel-title"><div className="step-icon">02</div><div><h2>Upload AI model</h2><p>Upload a ZIP archive containing model files and supporting documentation.</p></div></div>
                <label className="dropzone"><input type="file" accept=".zip,application/zip" onChange={e=>setModelFile(e.target.files?.[0]||null)}/><div className="upload-icon"><UploadCloud size={24}/></div><b>{modelFile ? modelFile.name : 'Choose a model ZIP file'}</b><span>{modelFile ? `${(modelFile.size/1024/1024).toFixed(2)} MB` : 'Drag and drop or browse your files'}</span><small>ZIP only · Maximum 100 MB</small></label>
              </div>
              <div className="panel"><div className="panel-title"><div className="step-icon optional">03</div><div><h2>Datasets <span className="optional-tag">OPTIONAL</span></h2><p>You can provide datasets now or add them later.</p></div></div>
                <div className="dataset-grid">{(['training','validation','test'] as const).map(kind=><label className="dataset-upload" key={kind}><div className="dataset-symbol"><Database size={18}/></div><b>{kind[0].toUpperCase()+kind.slice(1)} dataset</b><span>{datasets[kind]?.name || 'CSV file · Optional'}</span><input type="file" accept=".csv,text/csv" onChange={e=>setDatasets(old=>({...old,[kind]:e.target.files?.[0]||null}))}/><small>{datasets[kind]?'Change file':'Browse CSV'} <ArrowRight size={12}/></small></label>)}</div>
              </div>
              <div className="form-footer"><span>Fields marked optional can be completed later.</span><button className="primary" disabled={busy} onClick={create}>{busy?<><LoaderCircle className="spin" size={17}/> Creating...</>:<>Create assessment <ArrowRight size={17}/></>}</button></div>
            </div>
            <aside className="side-info"><div className="info-card"><ShieldCheck size={22}/><h3>Assessment process</h3><p>Your submission will be prepared for evaluation against the NIST AI Risk Management Framework.</p><div className="mini-step"><span>1</span> Model intake</div><div className="mini-step"><span>2</span> Technical inspection</div><div className="mini-step"><span>3</span> NIST assessment</div><div className="mini-step"><span>4</span> Assessment report</div></div><div className="security-note"><AlertCircle size={17}/><div><b>Upload safety</b><p>Model archives are inspected as ZIP metadata only. Uploaded code is not executed.</p></div></div></aside>
          </div>
        </section>}

        {page==='detail' && selected && <section>
          <div className="page-heading"><div><div className="eyebrow">ASSESSMENT #{selected.id}</div><h1>{selected.model_name}</h1><p>{selected.company_name} · {selected.model_type}</p></div><button className="secondary" onClick={()=>setPage('dashboard')}>Back to dashboard</button></div>
          <div className="detail-grid"><div className="panel"><h2>Model information</h2><div className="detail-row"><span>Company</span><b>{selected.company_name}</b></div><div className="detail-row"><span>Model</span><b>{selected.model_name}</b></div><div className="detail-row"><span>Type</span><b>{selected.model_type}</b></div><div className="detail-row"><span>Intended use</span><b>{selected.intended_use}</b></div><div className="detail-row"><span>Deployment context</span><b>{selected.deployment_context||'Not provided'}</b></div><div className="detail-row"><span>Status</span><b>{selected.status}</b></div></div>
            <div className="panel"><h2>Uploaded files</h2>{selected.uploads?.length ? selected.uploads.map(u=><div className="file-row" key={u.id}><FileArchive size={19}/><div><b>{u.original_filename}</b><small>{u.upload_kind} · {(u.size_bytes/1024).toFixed(1)} KB</small></div><CheckCircle2 className="file-check" size={17}/></div>):<p className="muted-text">No files uploaded.</p>}</div></div>
          {selected.uploads?.filter(u=>u.upload_kind==='model').map(u=><div className="panel inspection" key={u.id}><h2>ZIP inspection results</h2><p>Archive metadata inspection. No uploaded code was executed.</p><div className="inspection-grid">{['archive_valid','safe_to_extract','file_count','total_uncompressed_bytes'].map(k=><div className="inspection-stat" key={k}><small>{k.replaceAll('_',' ')}</small><b>{String((u.inspection as any)?.[k] ?? 'Not available')}</b></div>)}</div><h3>Detected model files</h3>{((u.inspection as any)?.model_files||[]).length ? <ul>{(u.inspection as any).model_files.map((f:string)=><li key={f}>{f}</li>)}</ul>:<p className="muted-text">No recognized model file extensions found.</p>}<h3>Configuration files</h3>{((u.inspection as any)?.configuration_files||[]).length ? <ul>{(u.inspection as any).configuration_files.map((f:string)=><li key={f}>{f}</li>)}</ul>:<p className="muted-text">No recognized configuration files found.</p>}{((u.inspection as any)?.warnings||[]).map((w:string)=><div className="warning-line" key={w}><AlertCircle size={15}/>{w}</div>)}</div>)}
          <div className="coming-panel"><Activity size={20}/><div><b>Preliminary NIST AI RMF assessment</b><p>Runs limited technical checks and identifies evidence still required. This is not a compliance certification.</p></div><button className="primary" disabled={busy} onClick={runAssessment}>{busy ? 'Running...' : 'Run assessment'}</button></div>
          {selected.findings && selected.findings.length > 0 && <div className="panel"><div className="section-heading"><div><h2>Assessment findings</h2><p>{selected.findings.length} preliminary findings · NIST AI RMF 1.0</p></div></div>{selected.findings.map(f=><div className="finding-row" key={f.id}><div className="finding-top"><b>{f.title}</b><span className={`finding-status ${f.status}`}>{f.status.replaceAll('_',' ')}</span></div><div className="finding-meta">{f.function} · {f.category} · {f.severity} · {f.source_type.replaceAll('_',' ')}</div><p><b>Evidence:</b> {f.evidence}</p><p><b>Assessment:</b> {f.rationale}</p></div>)}</div>}
        </section>}
      </div>
    </main>
  </div>
}
