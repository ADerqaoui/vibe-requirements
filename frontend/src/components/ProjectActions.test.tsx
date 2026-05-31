import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ProjectActions } from './ProjectActions'

describe('ProjectActions', () => {
  let clickSpy: ReturnType<typeof vi.fn>
  let createdLink: HTMLAnchorElement | null

  beforeEach(() => {
    clickSpy = vi.fn()
    createdLink = null
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => ({
        ok: true,
        blob: async () => new Blob(['# Brake Controller\n'], { type: 'text/markdown' }),
      })),
    )
    vi.stubGlobal('URL', {
      createObjectURL: vi.fn(() => 'blob:export'),
      revokeObjectURL: vi.fn(),
    })
    vi.spyOn(document, 'createElement').mockImplementation((tagName: string) => {
      const element = document.createElementNS('http://www.w3.org/1999/xhtml', tagName)
      if (tagName === 'a') {
        createdLink = element as HTMLAnchorElement
        createdLink.click = clickSpy
      }
      return element
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.unstubAllGlobals()
  })

  it('downloads a Markdown blob with slug filename', async () => {
    render(<ProjectActions projectId={7} projectName="Brake Controller!!" />)

    fireEvent.click(screen.getByRole('button', { name: 'Export Markdown' }))

    await waitFor(() => expect(clickSpy).toHaveBeenCalled())
    expect(fetch).toHaveBeenCalledWith('/api/projects/7/export.md')
    expect(createdLink?.download).toBe('brake-controller.md')
    expect(URL.createObjectURL).toHaveBeenCalled()
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:export')
  })

  it('is disabled without a selected Project', () => {
    render(<ProjectActions projectId={null} projectName={null} />)

    expect(screen.getByRole('button', { name: 'Export Markdown' })).toBeDisabled()
  })
})
