import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LocaleSwitcher } from '../LocaleSwitcher';

describe('LocaleSwitcher', () => {
  it('marks the active locale as aria-checked', () => {
    render(<LocaleSwitcher value="GH" onChange={() => undefined} />);
    expect(screen.getByRole('radio', { name: /Ghana/i })).toHaveAttribute(
      'aria-checked',
      'true',
    );
    expect(screen.getByRole('radio', { name: /Armenia/i })).toHaveAttribute(
      'aria-checked',
      'false',
    );
  });

  it('calls onChange with the chosen country code', async () => {
    const onChange = vi.fn();
    render(<LocaleSwitcher value="GH" onChange={onChange} />);
    await userEvent.click(screen.getByRole('radio', { name: /Armenia/i }));
    expect(onChange).toHaveBeenCalledWith('AM');
  });
});
