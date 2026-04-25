import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { SmsPreview } from '../SmsPreview';
import { LOCALES } from '@/lib/locales';

describe('SmsPreview', () => {
  it('shows the segment count for short messages', () => {
    render(
      <SmsPreview
        locale={LOCALES.GH}
        sms={{ text: 'short', char_count: 5, language: 'en-GH' }}
      />,
    );
    expect(screen.getByText(/5 chars · 1 segment/i)).toBeInTheDocument();
    expect(screen.getByText('short')).toBeInTheDocument();
  });

  it('counts multiple segments for longer messages', () => {
    const longText = 'x'.repeat(170);
    render(
      <SmsPreview
        locale={LOCALES.GH}
        sms={{ text: longText, char_count: 170 }}
      />,
    );
    expect(screen.getByText(/170 chars · 2 segments/i)).toBeInTheDocument();
  });

  it('renders the Tier 2 framing when emphasized', () => {
    render(
      <SmsPreview
        locale={LOCALES.GH}
        sms={{ text: 'x', char_count: 1 }}
        emphasized
      />,
    );
    expect(screen.getByRole('heading', { name: /Tier 2 — SMS/i })).toBeInTheDocument();
  });
});
