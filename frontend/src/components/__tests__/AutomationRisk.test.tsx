import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AutomationRisk } from '../AutomationRisk';
import { ghAmara } from '@/test/fixtures';

describe('AutomationRisk', () => {
  it('renders the LMIC-calibrated probability and tier for Amara', () => {
    const risk = ghAmara.profile.automation_risk!;
    render(<AutomationRisk risk={risk} />);

    expect(
      screen.getByRole('heading', { name: /AI readiness · automation risk to 2035/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/low risk/i)).toBeInTheDocument();
    // 0.23 * 100 → 23%
    expect(screen.getByText('23%')).toBeInTheDocument();
    // Raw FO probability appears at least once
    expect(screen.getAllByText(/41%/).length).toBeGreaterThan(0);
    // Sources line cites the three required sources
    expect(screen.getByText(/Frey & Osborne/i)).toBeInTheDocument();
    expect(screen.getByText(/ILO Future of Work/i)).toBeInTheDocument();
    // Wittgenstein appears in both the rationale and the sources line
    expect(screen.getAllByText(/Wittgenstein/i).length).toBeGreaterThan(0);
  });

  it('shows the ProfileCard NEET context narrative', () => {
    const risk = ghAmara.profile.automation_risk!;
    render(<AutomationRisk risk={risk} />);
    // Adjacent + durable skills are surfaced for the user
    expect(screen.getByText(/durable \(human-edge\) skills/i)).toBeInTheDocument();
    expect(screen.getByText(/adjacent skills to grow into/i)).toBeInTheDocument();
  });
});
