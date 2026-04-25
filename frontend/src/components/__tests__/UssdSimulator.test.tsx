import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { UssdSimulator } from '../UssdSimulator';
import { LOCALES } from '@/lib/locales';
import { ghAmara } from '@/test/fixtures';

describe('UssdSimulator', () => {
  const tree = ghAmara.human_layer.ussd_tree;

  it('starts in the dial-prompt state', () => {
    render(<UssdSimulator locale={LOCALES.GH} tree={tree} />);
    expect(screen.getByText(/press “dial \*789#/i)).toBeInTheDocument();
  });

  it('after dialing, shows the root menu and option buttons', async () => {
    render(<UssdSimulator locale={LOCALES.GH} tree={tree} />);
    await userEvent.click(screen.getByRole('button', { name: /dial \*789#/i }));
    expect(screen.getByText(/UNMAPPED \*789#/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /1\. View profile/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /2\. Skills/i })).toBeInTheDocument();
  });

  it('navigates into a child node and back via "0. Back"', async () => {
    render(<UssdSimulator locale={LOCALES.GH} tree={tree} />);
    await userEvent.click(screen.getByRole('button', { name: /dial \*789#/i }));
    await userEvent.click(screen.getByRole('button', { name: /1\. View profile/i }));
    expect(screen.getByText(/Amara, Accra/i)).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: /^0\. Back/i }));
    expect(screen.getByRole('button', { name: /1\. View profile/i })).toBeInTheDocument();
  });
});
