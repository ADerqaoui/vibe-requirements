type GenerationPanelHeaderProps = {
  blacklistCount: number
}

export function GenerationPanelHeader({ blacklistCount }: GenerationPanelHeaderProps) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-2">
      <h3 className="text-sm font-semibold text-neutral-900">Generate specs</h3>
      <span className="rounded bg-neutral-100 px-2 py-1 text-xs text-neutral-700">
        Blacklist: {blacklistCount}
      </span>
    </div>
  )
}

export default GenerationPanelHeader
