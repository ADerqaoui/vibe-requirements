import type { SpecInspection } from '../types/inspection'

type SpecInspectionDetailsProps = {
  inspection: SpecInspection
}

function verdictClasses(verdict: string): string {
  if (verdict === 'PASS') {
    return 'bg-green-100 text-green-700'
  }
  if (verdict === 'FAIL') {
    return 'bg-red-100 text-red-700'
  }
  return 'bg-amber-100 text-amber-700'
}

export function SpecInspectionDetails({ inspection }: SpecInspectionDetailsProps) {
  return (
    <div className="mt-3 rounded-md border border-neutral-200 bg-neutral-50 p-3">
      {inspection.selected_model_name && (
        <p className="mb-2 text-xs text-neutral-600">Inspected with: {inspection.selected_model_name}</p>
      )}
      {inspection.selected_prompt_name && (
        <p className="mb-2 text-xs text-neutral-600">Prompt: {inspection.selected_prompt_name}</p>
      )}
      <ul className="space-y-1">
        {inspection.findings.criteria.map((criterion) => (
          <li className="flex flex-wrap gap-2 text-xs" key={criterion.name}>
            <span className={`rounded px-2 py-0.5 font-medium ${verdictClasses(criterion.verdict)}`}>
              {criterion.verdict}
            </span>
            <span className="font-medium text-neutral-800">{criterion.name}</span>
            <span className="text-neutral-600">{criterion.note}</span>
          </li>
        ))}
      </ul>
      {inspection.findings.summary && <p className="mt-2 text-xs text-neutral-600">{inspection.findings.summary}</p>}
    </div>
  )
}
