// @vitest-environment jsdom

import '@testing-library/jest-dom/vitest'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { PredictionPanel } from './PredictionPanel'

describe('PredictionPanel', () => {
  it('labels confidence as GRD model confidence instead of disease probability', () => {
    render(
      <PredictionPanel
        result={{ label: '291', confidence: 0.874, model_name: 'rf', model_version: 'v1' }}
        evidenceCount={3}
      />,
    )

    expect(screen.getByText('87.4%')).toBeInTheDocument()
    expect(screen.getByText('confianza del modelo GRD')).toBeInTheDocument()
    expect(screen.queryByText(/probabilidad de enfermedad/i)).not.toBeInTheDocument()
  })
})
