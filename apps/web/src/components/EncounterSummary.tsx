type EncounterSummaryProps = {
  age: string
  sex: 'M' | 'F' | ''
  icd10Codes: string[]
  icd9Codes: string[]
}

export function EncounterSummary({ age, sex, icd10Codes, icd9Codes }: EncounterSummaryProps) {
  return (
    <section className="encounter-summary" aria-label="Resumen del episodio clínico">
      <div><span>Edad</span><strong>{age || 'No informada'}</strong></div>
      <div><span>Sexo</span><strong>{sex || 'No informado'}</strong></div>
      <div><span>ICD-10</span><strong>{icd10Codes.length}</strong></div>
      <div><span>Procedimientos</span><strong>{icd9Codes.length}</strong></div>
    </section>
  )
}
