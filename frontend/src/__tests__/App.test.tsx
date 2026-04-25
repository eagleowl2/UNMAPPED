import { describe, expect, it, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

beforeEach(() => {
  // Force the demo path so App doesn't try to hit a backend.
  vi.stubEnv('VITE_API_URL', '');
  vi.stubEnv('VITE_DEMO_MODE', 'true');
  vi.resetModules();
});

describe('App — full input → profile flow', () => {
  it('renders the Amara profile after submitting the GH sample', async () => {
    const { App } = await import('../App');
    render(<App />);

    const sampleBtn = screen.getByText(/try the amara story/i);
    await userEvent.click(sampleBtn);

    const submit = screen.getByRole('button', { name: /generate profile/i });
    expect(submit).toBeEnabled();
    await userEvent.click(submit);

    await waitFor(() =>
      expect(screen.getByRole('heading', { level: 2, name: /Amara/i })).toBeInTheDocument(),
    );
    expect(screen.getByText(/Phone Repair & Software Development/i)).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /smartphone/i })).toHaveAttribute(
      'aria-selected',
      'true',
    );
  });

  it('switches to SMS-only view when the SMS tier is chosen', async () => {
    const { App } = await import('../App');
    render(<App />);

    await userEvent.click(screen.getByText(/try the amara story/i));
    await userEvent.click(screen.getByRole('button', { name: /generate profile/i }));
    await waitFor(() =>
      expect(screen.getByRole('heading', { level: 2, name: /Amara/i })).toBeInTheDocument(),
    );

    await userEvent.click(screen.getByRole('tab', { name: /SMS/i }));
    expect(screen.getByRole('heading', { name: /Tier 2 — SMS/i })).toBeInTheDocument();
    // The full profile card should no longer be in the document.
    expect(screen.queryByRole('heading', { level: 2, name: /Amara/i })).not.toBeInTheDocument();
  });

  it('locale swap to Armenia loads the Ani sample', async () => {
    const { App } = await import('../App');
    render(<App />);

    await userEvent.click(screen.getByRole('radio', { name: /Armenia/i }));
    expect(screen.getByText(/try the ani story/i)).toBeInTheDocument();

    await userEvent.click(screen.getByText(/try the ani story/i));
    await userEvent.click(screen.getByRole('button', { name: /generate profile/i }));
    await waitFor(() =>
      expect(screen.getByRole('heading', { level: 2, name: /Ani/i })).toBeInTheDocument(),
    );
    // Gyumri appears in the profile card location AND in the USSD node text;
    // either presence is fine — we just want to confirm the AM mock loaded.
    expect(screen.getAllByText(/Gyumri/i).length).toBeGreaterThan(0);
  });
});
