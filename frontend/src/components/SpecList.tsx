import type { Spec } from '../types/spec'

type SpecListProps = {
  specs: Spec[]
}

export function SpecList({ specs }: SpecListProps) {
  if (specs.length === 0) {
    return <p className="mt-2 text-sm text-neutral-500">No specs accepted yet.</p>
  }

  return (
    <ul className="mt-2 space-y-2">
      {specs.map((spec) => (
        <li className="rounded-md border border-neutral-200 bg-white p-3 text-sm" key={spec.id}>
          {spec.statement}
        </li>
      ))}
    </ul>
  )
}
