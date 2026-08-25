import type { FormEvent } from 'react'

import { ArrowIcon } from '../icons'

type ClinicalIntakePanelProps = {
  age: string
  sex: 'M' | 'F' | ''
  icd10: string
  icd9: string
  pending: boolean
  evidenceCount: number
  onAgeChange: (value: string) => void
  onSexChange: (value: 'M' | 'F' | '') => void
  onIcd10Change: (value: string) => void
  onIcd9Change: (value: string) => void
  onSubmit: (event: FormEvent<HTMLFormElement>) => void
}

export function ClinicalIntakePanel(props: ClinicalIntakePanelProps) {
  return (
    <section className="evaluation-panel">
      <div className="section-heading">
        <p className="eyebrow">Nueva evaluación</p>
        <h2>Contexto clínico estructurado</h2>
        <p>Ingresa las variables que consume el modelo GRD. Los códigos pueden separarse por espacios, comas o punto y coma.</p>
      </div>

      <form className="clinical-form" onSubmit={props.onSubmit}>
        <div className="field-grid two-columns">
          <label>
            <span>Edad</span>
            <input min="0" max="120" inputMode="numeric" type="number" value={props.age} onChange={(event) => props.onAgeChange(event.target.value)} placeholder="65" />
          </label>
          <label>
            <span>Sexo</span>
            <select value={props.sex} onChange={(event) => props.onSexChange(event.target.value as 'M' | 'F' | '')}>
              <option value="">No informado</option>
              <option value="F">Femenino</option>
              <option value="M">Masculino</option>
            </select>
          </label>
        </div>

        <label>
          <span>ICD-10</span>
          <textarea rows={4} value={props.icd10} onChange={(event) => props.onIcd10Change(event.target.value)} placeholder="E11.9, I10" />
        </label>
        <label>
          <span>ICD-9 / procedimientos</span>
          <textarea rows={3} value={props.icd9} onChange={(event) => props.onIcd9Change(event.target.value)} placeholder="39.61" />
        </label>

        <div className="form-footer">
          <div className="evidence-summary">
            <span>{props.evidenceCount}</span>
            <small>códigos clínicos cargados</small>
          </div>
          <button type="submit" disabled={props.pending}>
            {props.pending ? 'Analizando…' : 'Analizar caso'} <ArrowIcon />
          </button>
        </div>
      </form>
    </section>
  )
}
