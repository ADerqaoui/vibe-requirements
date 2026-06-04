import type { SpecTreeNode } from '../types/spec'
import { SpecList } from './SpecList'

type GenerationSpecSectionProps = {
  classifyingSpecIds: Set<number>
  onSelectSpec?: (spec: SpecTreeNode) => void
  onSpecChanged: () => void
  routerEnabled?: boolean
  selectedSpecId: number | null
  specs: SpecTreeNode[]
}

export function GenerationSpecSection({
  classifyingSpecIds,
  onSelectSpec,
  onSpecChanged,
  routerEnabled = false,
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
        routerEnabled={routerEnabled}
        selectedSpecId={selectedSpecId}
        specs={specs}
      />
    </>
  )
}
