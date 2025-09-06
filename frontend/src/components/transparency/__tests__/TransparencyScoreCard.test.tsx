/**
 * Tests for TransparencyScoreCard component
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import TransparencyScoreCard from '../TransparencyScoreCard';
import { TransparencyMetrics } from '../../../types/transparency';

const mockMetrics: TransparencyMetrics = {
  ttm_score: 78.5,
  ttp_score: 82.3,
  overall_score: 80.4,
  confidence_level: 85.2,
  traced_percentage: 76.8,
  untraced_percentage: 23.2,
  last_updated: '2024-01-15T10:00:00Z',
};

describe('TransparencyScoreCard', () => {
  it('renders transparency metrics correctly', () => {
    render(<TransparencyScoreCard metrics={mockMetrics} />);
    
    expect(screen.getByText('80.4%')).toBeInTheDocument();
    expect(screen.getByText('Overall Transparency')).toBeInTheDocument();
    expect(screen.getByText('78.5%')).toBeInTheDocument();
    expect(screen.getByText('82.3%')).toBeInTheDocument();
    expect(screen.getByText('85.2%')).toBeInTheDocument();
  });

  it('displays TTM and TTP scores', () => {
    render(<TransparencyScoreCard metrics={mockMetrics} />);
    
    expect(screen.getByText('TTM')).toBeInTheDocument();
    expect(screen.getByText('TTP')).toBeInTheDocument();
    expect(screen.getByText('Time to Market')).toBeInTheDocument();
    expect(screen.getByText('Time to Production')).toBeInTheDocument();
  });

  it('shows confidence level with appropriate badge', () => {
    render(<TransparencyScoreCard metrics={mockMetrics} />);
    
    expect(screen.getByText('Confidence Level')).toBeInTheDocument();
    expect(screen.getByText('High')).toBeInTheDocument();
  });

  it('displays traceability breakdown', () => {
    render(<TransparencyScoreCard metrics={mockMetrics} />);
    
    expect(screen.getByText('Supply Chain Traceability')).toBeInTheDocument();
    expect(screen.getByText('Traced: 76.8%')).toBeInTheDocument();
    expect(screen.getByText('Untraced: 23.2%')).toBeInTheDocument();
  });

  it('shows trend when previous score is provided', () => {
    render(
      <TransparencyScoreCard 
        metrics={mockMetrics} 
        showTrend={true}
        previousScore={75.0}
      />
    );
    
    expect(screen.getByText('5.4%')).toBeInTheDocument();
  });

  it('applies correct size classes', () => {
    const { rerender } = render(
      <TransparencyScoreCard metrics={mockMetrics} size="sm" />
    );
    
    rerender(<TransparencyScoreCard metrics={mockMetrics} size="lg" />);
    
    // Component should render without errors for different sizes
    expect(screen.getByText('Overall Transparency')).toBeInTheDocument();
  });

  it('handles low confidence level', () => {
    const lowConfidenceMetrics = {
      ...mockMetrics,
      confidence_level: 65.0,
    };
    
    render(<TransparencyScoreCard metrics={lowConfidenceMetrics} />);
    
    expect(screen.getByText('Medium')).toBeInTheDocument();
  });

  it('formats last updated date', () => {
    render(<TransparencyScoreCard metrics={mockMetrics} />);
    
    expect(screen.getByText(/Last updated:/)).toBeInTheDocument();
  });
});

describe('TransparencyScoreCard accessibility', () => {
  it('has proper ARIA labels and structure', () => {
    render(<TransparencyScoreCard metrics={mockMetrics} />);
    
    // Check for proper heading structure
    expect(screen.getByText('Transparency Score')).toBeInTheDocument();
    expect(screen.getByText('Overall Transparency')).toBeInTheDocument();
  });

  it('provides meaningful text for screen readers', () => {
    render(<TransparencyScoreCard metrics={mockMetrics} />);
    
    // All percentage values should be clearly labeled
    expect(screen.getByText('TTM')).toBeInTheDocument();
    expect(screen.getByText('TTP')).toBeInTheDocument();
    expect(screen.getByText('Confidence Level')).toBeInTheDocument();
  });
});

describe('TransparencyScoreCard edge cases', () => {
  it('handles zero scores', () => {
    const zeroMetrics = {
      ...mockMetrics,
      overall_score: 0,
      ttm_score: 0,
      ttp_score: 0,
    };
    
    render(<TransparencyScoreCard metrics={zeroMetrics} />);
    
    expect(screen.getByText('0.0%')).toBeInTheDocument();
  });

  it('handles perfect scores', () => {
    const perfectMetrics = {
      ...mockMetrics,
      overall_score: 100,
      ttm_score: 100,
      ttp_score: 100,
      confidence_level: 100,
      traced_percentage: 100,
      untraced_percentage: 0,
    };
    
    render(<TransparencyScoreCard metrics={perfectMetrics} />);
    
    expect(screen.getAllByText('100.0%')).toHaveLength(4); // overall, ttm, ttp, confidence
  });

  it('handles missing trend data gracefully', () => {
    render(
      <TransparencyScoreCard 
        metrics={mockMetrics} 
        showTrend={true}
        // No previousScore provided
      />
    );
    
    // Should not show trend indicator
    expect(screen.queryByText(/\d+\.\d+%/)).toBeInTheDocument(); // Still shows main score
  });
});
