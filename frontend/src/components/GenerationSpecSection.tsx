import type { SpecTreeNode } from '../types/spec'
import { SpecList } from './SpecList'

type GenerationSpecSectionProps = {
  classifyingSpecIds: Set<number>
  onSelectSpec?: (spec: SpecTreeNode) => void
  onSpecChanged: () => void
  selectedSpecId: number | null
  specs: SpecTreeNode[]
}

export function GenerationSpecSection({
  classifyingSpecIds,
  onSelectSpec,
  onSpecChanged,
  selectedSpecId,
  specs,
}: GenerationSpecSectionProps) {
  return (
    <>
      <h3 className="mt-5 text-sm font-semibold text-neutral-900">Specs</h3>
      <SpecList
        classifyingSpecIds={classifyingSpecIds}
        onSelectSpec={onSelectSpec}
        onSpecChanged={onSpecChanged}
        selectedSpecId={selectedSpecId}
        specs={specs}
      />
    </>
  )
}
