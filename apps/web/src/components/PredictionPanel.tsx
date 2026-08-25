import type { PredictionResponse } from '../api'

import { ModelIcon } from '../icons'

type PredictionPanelProps = {
  result: PredictionResponse | null
  error?: string
  evidenceCount: number
}

export function PredictionPanel({ result, error = '', evidenceCount }: PredictionPanelProps) {
  return (
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
            <span>confianza del modelo GRD</span>
          </div>
          <dl className="model-metadata">
            <div><dt>Modelo</dt><dd>{result.model_name}</dd></div>
            <div><dt>Versión</dt><dd>{result.model_version}</dd></div>
            <div><dt>Evidencia</dt><dd>{evidenceCount} códigos</dd></div>
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
        <p>La confianza corresponde al clasificador GRD; no representa probabilidad de enfermedad ni sustituye evaluación profesional.</p>
      </div>
    </aside>
  )
}
