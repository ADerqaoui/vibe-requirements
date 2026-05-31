export type InspectionVerdict = 'PASS' | 'FAIL' | 'UNCLEAR'

export type InspectionCriterion = {
  name: string
  verdict: InspectionVerdict
  note: string
}

export type InspectionFindings = {
  criteria: InspectionCriterion[]
  summary: string | null
}

export type SpecInspection = {
  id: number
  spec_id: number
  model_id: number
  findings: InspectionFindings
  passes: number
  created_at: string
}
