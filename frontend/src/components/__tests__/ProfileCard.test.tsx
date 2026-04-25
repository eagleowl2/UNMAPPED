import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ProfileCard } from '../ProfileCard';
import { LOCALES } from '@/lib/locales';
import { ghAmara } from '@/test/fixtures';

describe('ProfileCard', () => {
  it('renders the canonical Amara profile fields', () => {
    render(<ProfileCard locale={LOCALES.GH} data={ghAmara} source="live" />);

    // Display name + headline + zero-credential badge
    expect(screen.getByRole('heading', { level: 2, name: /Amara/i })).toBeInTheDocument();
    expect(screen.getByText(/Phone Repair & Software Development/i)).toBeInTheDocument();
    expect(screen.getByText(/Zero-credential verified/i)).toBeInTheDocument();

    // Both skills surface with their tier chips and ISCO codes
    expect(screen.getByText('Phone Repair')).toBeInTheDocument();
    expect(screen.getByText('Software Development')).toBeInTheDocument();
    expect(screen.getByText('Established')).toBeInTheDocument();
    expect(screen.getByText('Developing')).toBeInTheDocument();
    expect(screen.getByText('ISCO-08:7421')).toBeInTheDocument();
    expect(screen.getByText('ISCO-08:2512')).toBeInTheDocument();

    // Confidence percentages render rounded
    expect(screen.getByText('68%')).toBeInTheDocument();
    expect(screen.getByText('52%')).toBeInTheDocument();

    // Ownership statement
    expect(screen.getByLabelText(/ownership and control/i)).toBeInTheDocument();
  });

  it('badges the parser source', () => {
    render(<ProfileCard locale={LOCALES.GH} data={ghAmara} source="mock-fallback" />);
    expect(screen.getByText(/offline fallback/i)).toBeInTheDocument();
  });
});
