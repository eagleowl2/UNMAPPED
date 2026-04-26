import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { UssdSimulator } from '../UssdSimulator';
import { LOCALES } from '@/lib/locales';
import { ghAmara } from '@/test/fixtures';

describe('UssdSimulator', () => {
  const menu = ghAmara.profile.ussd_menu;

  it('starts in the dial-prompt state', () => {
    render(<UssdSimulator locale={LOCALES.GH} menu={menu} />);
    expect(screen.getByText(/press “dial \*789#/i)).toBeInTheDocument();
  });

  it('after dialing, renders the parser-supplied menu lines', async () => {
    render(<UssdSimulator locale={LOCALES.GH} menu={menu} />);
    await userEvent.click(screen.getByRole('button', { name: /dial \*789#/i }));
    expect(screen.getByText(/UNMAPPED \*789#/i)).toBeInTheDocument();
    expect(screen.getByText(/1\. View profile/i)).toBeInTheDocument();
    expect(screen.getByText(/Wage signal/i)).toBeInTheDocument();
  });

  it('hangs up when toggled', async () => {
    render(<UssdSimulator locale={LOCALES.GH} menu={menu} />);
    await userEvent.click(screen.getByRole('button', { name: /dial \*789#/i }));
    await userEvent.click(screen.getByRole('button', { name: /hang up/i }));
    expect(screen.getByText(/press “dial \*789#/i)).toBeInTheDocument();
  });
});
