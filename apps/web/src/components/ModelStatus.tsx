type ModelStatusProps = {
  ready?: boolean
}

export function ModelStatus({ ready = true }: ModelStatusProps) {
  return (
    <div className="system-state" aria-label="Estado del modelo">
      <span className="status-dot" /> {ready ? 'Modelo disponible' : 'Modelo no disponible'}
    </div>
  )
}
