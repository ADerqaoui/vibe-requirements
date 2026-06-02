export type GenerationParent = {
  kind: 'need' | 'spec'
  id: number
}

export function parentFromNeedId(needId: number | null | undefined): GenerationParent | null {
  if (needId === null || needId === undefined) {
    return null
  }
  return { kind: 'need', id: needId }
}

export function parentKey(parent: GenerationParent | null): string {
  return parent === null ? 'none' : `${parent.kind}:${parent.id}`
}
