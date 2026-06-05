import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { SpecEditor } from './SpecEditor'

describe('SpecEditor', () => {
  it('prefills, saves trimmed text, and blocks empty saves', async () => {
    const onSave = vi.fn().mockResolvedValue(undefined)
    render(<SpecEditor initialText="Original text" onCancel={vi.fn()} onSave={onSave} />)

    const editor = screen.getByLabelText('Spec text')
    expect(editor).toHaveValue('Original text')
    fireEvent.change(editor, { target: { value: '   ' } })
    expect(screen.getByRole('button', { name: 'Save' })).toBeDisabled()

    fireEvent.change(editor, { target: { value: ' Edited text ' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => expect(onSave).toHaveBeenCalledWith('Edited text'))
  })
})
