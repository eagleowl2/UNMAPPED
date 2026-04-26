import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ProfileCard } from '../ProfileCard';
import { LOCALES } from '@/lib/locales';
import { ghAmara } from '@/test/fixtures';

describe('ProfileCard', () => {
  it('renders the canonical Amara profile fields', () => {
    render(<ProfileCard locale={LOCALES.GH} data={ghAmara} source="live" />);

    // Pseudonym + location
    expect(screen.getByRole('heading', { level: 2, name: /Amara/i })).toBeInTheDocument();
    expect(screen.getByText(/Accra, Greater Accra/i)).toBeInTheDocument();

    // The two econometric signals are first-class
    expect(screen.getByRole('heading', { name: /Wage signal/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /Growth signal/i })).toBeInTheDocument();
    expect(screen.getByText('GHS 38 / day')).toBeInTheDocument();

    // Skills with confidence
    expect(screen.getByRole('heading', { level: 4, name: 'Phone Repair' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 4, name: 'Software Development' })).toBeInTheDocument();

    // Network entry channel
    expect(screen.getByText(/Mobile-money cooperative/i)).toBeInTheDocument();

    // Ownership statement
    expect(screen.getByLabelText(/ownership and control/i)).toBeInTheDocument();
  });

  it('badges the parser source', () => {
    render(<ProfileCard locale={LOCALES.GH} data={ghAmara} source="mock-fallback" />);
    expect(screen.getByText(/offline fallback/i)).toBeInTheDocument();
  });
});
