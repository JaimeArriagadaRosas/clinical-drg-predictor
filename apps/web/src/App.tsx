import { FormEvent, useMemo, useState } from 'react'

import { predictDrg, type PredictionResponse } from './api'
import { ArrowIcon, ClinicalIcon, DatabaseIcon, HistoryIcon, ModelIcon } from './icons'

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

  const evidenceCount = useMemo(
    () => parseCodes(icd10).length + parseCodes(icd9).length,
    [icd10, icd9],
  )

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setPending(true)
    try {
      const numericAge = age === '' ? undefined : Number(age)
      const prediction = await predictDrg({
        icd10_codes: parseCodes(icd10),
        icd9_codes: parseCodes(icd9),
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
        <div className="system-state"><span className="status-dot" /> API local</div>
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
          <section className="evaluation-panel">
            <div className="section-heading">
              <p className="eyebrow">Nueva evaluación</p>
              <h2>Contexto clínico estructurado</h2>
              <p>Ingresa las variables que consume el modelo GRD. Los códigos pueden separarse por espacios, comas o punto y coma.</p>
            </div>

            <form className="clinical-form" onSubmit={handleSubmit}>
              <div className="field-grid two-columns">
                <label>
                  <span>Edad</span>
                  <input min="0" max="120" inputMode="numeric" type="number" value={age} onChange={(event) => setAge(event.target.value)} placeholder="65" />
                </label>
                <label>
                  <span>Sexo</span>
                  <select value={sex} onChange={(event) => setSex(event.target.value as 'M' | 'F' | '')}>
                    <option value="">No informado</option>
                    <option value="F">Femenino</option>
                    <option value="M">Masculino</option>
                  </select>
                </label>
              </div>

              <label>
                <span>ICD-10</span>
                <textarea rows={4} value={icd10} onChange={(event) => setIcd10(event.target.value)} placeholder="E11.9, I10" />
              </label>
              <label>
                <span>ICD-9 / procedimientos</span>
                <textarea rows={3} value={icd9} onChange={(event) => setIcd9(event.target.value)} placeholder="39.61" />
              </label>

              <div className="form-footer">
                <div className="evidence-summary">
                  <span>{evidenceCount}</span>
                  <small>códigos clínicos cargados</small>
                </div>
                <button type="submit" disabled={pending}>
                  {pending ? 'Analizando…' : 'Analizar caso'} <ArrowIcon />
                </button>
              </div>
            </form>
          </section>

          <aside className="result-panel" aria-live="polite">
            <div className="section-heading compact">
              <p className="eyebrow">Resultado</p>
              <h2>Predicción GRD</h2>
            </div>

            {result ? (
              <div className="prediction-result">
                <div className="result-code">{result.label}</div>
                <div className="confidence-block">
                  <strong>{(result.confidence * 100).toFixed(1)}%</strong>
                  <span>confianza del modelo</span>
                </div>
                <dl className="model-metadata">
                  <div><dt>Modelo</dt><dd>{result.model_name}</dd></div>
                  <div><dt>Versión</dt><dd>{result.model_version}</dd></div>
                </dl>
              </div>
            ) : (
              <div className="empty-result">
                <ModelIcon />
                <strong>Sin predicción todavía</strong>
                <p>El resultado aparecerá aquí sin reemplazar el contexto ingresado.</p>
              </div>
            )}

            {error && <div className="error-message" role="alert">{error}</div>}

            <div className="clinical-disclaimer">
              <strong>Uso académico</strong>
              <p>Esta interfaz demuestra soporte a decisión e interoperabilidad. No constituye diagnóstico médico ni sustituye evaluación profesional.</p>
            </div>
          </aside>
        </main>
      </div>
    </div>
  )
}
