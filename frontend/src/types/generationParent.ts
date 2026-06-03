export type GenerationParent =
  | { kind: 'need'; id: number }
  | { kind: 'spec'; id: number; layer_id: number }

export function parentFromNeedId(needId: number | null | undefined): GenerationParent | null {
  if (needId === null || needId === undefined) {
    return null
  }
  return { kind: 'need', id: needId }
}

export function parentKey(parent: GenerationParent | null): string {
  return parent === null ? 'none' : `${parent.kind}:${parent.id}`
}
