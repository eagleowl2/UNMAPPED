import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ConstraintTierSwitcher } from '../ConstraintTierSwitcher';

describe('ConstraintTierSwitcher', () => {
  it('marks the active tier with aria-selected', () => {
    render(<ConstraintTierSwitcher value="sms" onChange={() => undefined} />);
    expect(screen.getByRole('tab', { name: /SMS/i })).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByRole('tab', { name: /Smartphone/i })).toHaveAttribute('aria-selected', 'false');
    expect(screen.getByRole('tab', { name: /USSD/i })).toHaveAttribute('aria-selected', 'false');
  });

  it('calls onChange when a different tier is clicked', async () => {
    const onChange = vi.fn();
    render(<ConstraintTierSwitcher value="smartphone" onChange={onChange} />);
    await userEvent.click(screen.getByRole('tab', { name: /USSD/i }));
    expect(onChange).toHaveBeenCalledWith('ussd');
  });
});
