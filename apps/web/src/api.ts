export type PredictionRequest = {
  icd10_codes: string[]
  icd9_codes: string[]
  age?: number
  sex?: 'M' | 'F'
}

export type PredictionResponse = {
  label: string
  confidence: number
  model_name: string
  model_version: string
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

export async function predictDrg(payload: PredictionRequest): Promise<PredictionResponse> {
  const response = await fetch(`${API_BASE_URL}/v1/predictions/drg`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const errorBody = (await response.json().catch(() => null)) as { detail?: string } | null
    throw new Error(errorBody?.detail ?? `Prediction failed with HTTP ${response.status}`)
  }

  return (await response.json()) as PredictionResponse
}
