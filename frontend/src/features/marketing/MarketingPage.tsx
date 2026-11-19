import React from 'react';
import { KPICard } from '../../components/common/KPICard';

export const MarketingPage: React.FC = () => {
  return (
    <div data-testid="marketing-page">
      <div style={{ marginBottom: '1.25rem' }}>
        <h1
          style={{ margin: '0 0 0.25rem', fontSize: '1.625rem', fontWeight: 700, color: '#ffffff' }}
        >
          Marketing Campaign ROI & Acquisition
        </h1>
        <p style={{ margin: 0, color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>
          Omnichannel spend efficiency, CAC, ROAS, click-through conversions, and campaign flights.
        </p>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: '1rem',
        }}
      >
        <KPICard
          title="Total Marketing Spend"
          value={420000}
          format="currency"
          trend={{ value: 5.1, direction: 'up', period: '40 campaigns' }}
        />
        <KPICard
          title="Blended CAC"
          value={168}
          format="currency"
          trend={{ value: 8.2, direction: 'down', isPositive: true, period: 'vs benchmark' }}
        />
        <KPICard
          title="Return on Ad Spend (ROAS)"
          value={4.6}
          format="raw"
          subtitle="4.6x revenue per $ spend"
          trend={{ value: 12.3, direction: 'up', isPositive: true }}
        />
        <KPICard
          title="Conversion Rate"
          value={3.8}
          format="percent"
          trend={{ value: 0.4, direction: 'up', period: 'vs previous flight' }}
        />
      </div>
    </div>
  );
};
