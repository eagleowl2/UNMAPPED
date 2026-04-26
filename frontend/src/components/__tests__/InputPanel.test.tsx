import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { InputPanel } from '../InputPanel';
import { LOCALES } from '@/lib/locales';

const baseProps = {
  locale: LOCALES.GH,
  value: '',
  onChange: vi.fn(),
  onSubmit: vi.fn(),
  loading: false,
};

describe('InputPanel', () => {
  it('disables submit when input is empty', () => {
    render(<InputPanel {...baseProps} />);
    expect(screen.getByRole('button', { name: /generate profile/i })).toBeDisabled();
  });

  it('enables submit when input has non-whitespace content', () => {
    render(<InputPanel {...baseProps} value="hi" />);
    expect(screen.getByRole('button', { name: /generate profile/i })).toBeEnabled();
  });

  it('shows the localized sample-button label', () => {
    render(<InputPanel {...baseProps} locale={LOCALES.AM} />);
    expect(screen.getByText(LOCALES.AM.sampleLabel)).toBeInTheDocument();
  });

  it('clicking the sample button populates the textarea via onChange', async () => {
    const onChange = vi.fn();
    render(<InputPanel {...baseProps} onChange={onChange} />);
    await userEvent.click(screen.getByText(LOCALES.GH.sampleLabel));
    expect(onChange).toHaveBeenCalledWith(LOCALES.GH.sample);
  });

  it('Cmd/Ctrl+Enter submits when input is present', async () => {
    const onSubmit = vi.fn();
    render(<InputPanel {...baseProps} value="something" onSubmit={onSubmit} />);
    const textarea = screen.getByLabelText(/raw personal description/i);
    textarea.focus();
    await userEvent.keyboard('{Control>}{Enter}{/Control}');
    expect(onSubmit).toHaveBeenCalled();
  });

  it('renders a busy state while loading', () => {
    render(<InputPanel {...baseProps} value="x" loading />);
    expect(screen.getByRole('button', { name: /parsing/i })).toBeDisabled();
  });
});
