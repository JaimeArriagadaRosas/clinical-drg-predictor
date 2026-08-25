import { type FormEvent, useMemo, useState } from 'react'

import { predictDrg, type PredictionResponse } from './api'
import { ClinicalIntakePanel } from './components/ClinicalIntakePanel'
import { EncounterSummary } from './components/EncounterSummary'
import { ModelStatus } from './components/ModelStatus'
import { PredictionPanel } from './components/PredictionPanel'
import { ClinicalIcon, DatabaseIcon, HistoryIcon, ModelIcon } from './icons'

const parseCodes = (value: string) =>
  value
    .split(/[\s,;]+/)
    .map((code) => code.trim())
    .filter(Boolean)

export default function App() {
  const [age, setAge] = useState('')
  const [sex, setSex] = useState<'M' | 'F' | ''>('')
  const [icd10, setIcd10] = useState('')
  const [icd9, setIcd9] = useState('')
  const [result, setResult] = useState<PredictionResponse | null>(null)
  const [error, setError] = useState('')
  const [pending, setPending] = useState(false)

  const icd10Codes = useMemo(() => parseCodes(icd10), [icd10])
  const icd9Codes = useMemo(() => parseCodes(icd9), [icd9])
  const evidenceCount = icd10Codes.length + icd9Codes.length

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setPending(true)
    try {
      const numericAge = age === '' ? undefined : Number(age)
      const prediction = await predictDrg({
        icd10_codes: icd10Codes,
        icd9_codes: icd9Codes,
        ...(numericAge === undefined ? {} : { age: numericAge }),
        ...(sex === '' ? {} : { sex }),
      })
      setResult(prediction)
    } catch (requestError) {
      setResult(null)
      setError(requestError instanceof Error ? requestError.message : 'No fue posible completar la predicción.')
    } finally {
      setPending(false)
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-lockup">
          <div className="brand-mark"><ClinicalIcon /></div>
          <div>
            <p className="eyebrow">Clinical Intelligence Platform</p>
            <h1>GRD Decision Support</h1>
          </div>
        </div>
        <ModelStatus />
      </header>

      <div className="workspace">
        <aside className="sidebar" aria-label="Navegación principal">
          <nav>
            <a className="nav-item active" href="#evaluation"><ClinicalIcon /> Evaluación</a>
            <a className="nav-item" href="#history"><HistoryIcon /> Historial</a>
            <a className="nav-item" href="#model"><ModelIcon /> Modelo</a>
            <a className="nav-item" href="#data"><DatabaseIcon /> Datos</a>
          </nav>
          <div className="sidebar-note">
            <span>Interoperabilidad</span>
            <strong>FHIR adapter enabled</strong>
            <small>FHIR se usa como frontera clínica, no como motor de almacenamiento.</small>
          </div>
        </aside>

        <main className="main-grid" id="evaluation">
          <div>
            <ClinicalIntakePanel
              age={age}
              sex={sex}
              icd10={icd10}
              icd9={icd9}
              pending={pending}
              evidenceCount={evidenceCount}
              onAgeChange={setAge}
              onSexChange={setSex}
              onIcd10Change={setIcd10}
              onIcd9Change={setIcd9}
              onSubmit={handleSubmit}
            />
            <EncounterSummary age={age} sex={sex} icd10Codes={icd10Codes} icd9Codes={icd9Codes} />
          </div>
          <PredictionPanel result={result} error={error} evidenceCount={evidenceCount} />
        </main>
      </div>
    </div>
  )
}
