/**
 * Tests for GapAnalysisPanel component
 */
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import GapAnalysisPanel from '../GapAnalysisPanel';
import { GapAnalysisItem } from '../../../types/transparency';

const mockGaps: GapAnalysisItem[] = [
  {
    id: 'gap-1',
    type: 'missing_supplier',
    severity: 'critical',
    title: 'Missing Packaging Supplier',
    description: 'No supplier information for packaging materials',
    impact_score: 15.2,
    affected_nodes: ['node-1'],
    recommendations: [
      'Identify and onboard packaging supplier',
      'Request transparency documentation',
    ],
    estimated_improvement: 8.5,
  },
  {
    id: 'gap-2',
    type: 'unconfirmed_order',
    severity: 'high',
    title: 'Pending Dye Confirmation',
    description: 'Dye supplier has not confirmed order details',
    impact_score: 8.7,
    affected_nodes: ['node-4'],
    recommendations: [
      'Follow up with supplier',
      'Provide confirmation template',
    ],
    estimated_improvement: 5.2,
  },
  {
    id: 'gap-3',
    type: 'low_transparency',
    severity: 'medium',
    title: 'Low Transparency Score',
    description: 'Supplier has low transparency metrics',
    impact_score: 6.3,
    affected_nodes: ['node-2'],
    recommendations: [
      'Provide transparency training',
      'Implement tracking systems',
    ],
    estimated_improvement: 3.8,
  },
];

describe('GapAnalysisPanel', () => {
  it('renders gap analysis summary correctly', () => {
    render(<GapAnalysisPanel gaps={mockGaps} />);
    
    expect(screen.getByText('Gap Analysis')).toBeInTheDocument();
    expect(screen.getByText(/3 gaps identified/)).toBeInTheDocument();
    expect(screen.getByText(/17.5% potential improvement/)).toBeInTheDocument();
  });

  it('displays summary statistics', () => {
    render(<GapAnalysisPanel gaps={mockGaps} />);
    
    expect(screen.getByText('1')).toBeInTheDocument(); // Critical count
    expect(screen.getByText('Critical')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument(); // High count
    expect(screen.getByText('High Priority')).toBeInTheDocument();
    expect(screen.getByText('+17.5%')).toBeInTheDocument(); // Potential gain
  });

  it('shows filter buttons with counts', () => {
    render(<GapAnalysisPanel gaps={mockGaps} />);
    
    expect(screen.getByText('All')).toBeInTheDocument();
    expect(screen.getByText('Critical (1)')).toBeInTheDocument();
    expect(screen.getByText('High (1)')).toBeInTheDocument();
    expect(screen.getByText('Medium (1)')).toBeInTheDocument();
  });

  it('filters gaps by severity', () => {
    render(<GapAnalysisPanel gaps={mockGaps} />);
    
    // Click critical filter
    fireEvent.click(screen.getByText('Critical (1)'));
    
    // Should only show critical gap
    expect(screen.getByText('Missing Packaging Supplier')).toBeInTheDocument();
    expect(screen.queryByText('Pending Dye Confirmation')).not.toBeInTheDocument();
  });

  it('expands gap details when clicked', () => {
    render(<GapAnalysisPanel gaps={mockGaps} />);
    
    // Initially recommendations should not be visible
    expect(screen.queryByText('Identify and onboard packaging supplier')).not.toBeInTheDocument();
    
    // Click on gap to expand
    fireEvent.click(screen.getByText('Missing Packaging Supplier'));
    
    // Now recommendations should be visible
    expect(screen.getByText('Recommendations')).toBeInTheDocument();
    expect(screen.getByText('Identify and onboard packaging supplier')).toBeInTheDocument();
  });

  it('calls onGapClick when gap is clicked', () => {
    const mockOnGapClick = jest.fn();
    render(<GapAnalysisPanel gaps={mockGaps} onGapClick={mockOnGapClick} />);
    
    fireEvent.click(screen.getByText('Missing Packaging Supplier'));
    
    expect(mockOnGapClick).toHaveBeenCalledWith(mockGaps[0]);
  });

  it('calls onRecommendationAction when action button is clicked', () => {
    const mockOnRecommendationAction = jest.fn();
    render(
      <GapAnalysisPanel 
        gaps={mockGaps} 
        onRecommendationAction={mockOnRecommendationAction}
      />
    );
    
    // Expand gap first
    fireEvent.click(screen.getByText('Missing Packaging Supplier'));
    
    // Click action button
    fireEvent.click(screen.getAllByText('Take Action')[0]);
    
    expect(mockOnRecommendationAction).toHaveBeenCalledWith(
      'gap-1',
      'Identify and onboard packaging supplier'
    );
  });

  it('displays correct severity badges and icons', () => {
    render(<GapAnalysisPanel gaps={mockGaps} />);
    
    expect(screen.getByText('critical')).toBeInTheDocument();
    expect(screen.getByText('high')).toBeInTheDocument();
    expect(screen.getByText('medium')).toBeInTheDocument();
  });

  it('shows no gaps message when empty', () => {
    render(<GapAnalysisPanel gaps={[]} />);
    
    expect(screen.getByText('No gaps found!')).toBeInTheDocument();
    expect(screen.getByText('Your supply chain transparency is excellent.')).toBeInTheDocument();
  });

  it('sorts gaps by severity and impact', () => {
    render(<GapAnalysisPanel gaps={mockGaps} />);
    
    const gapTitles = screen.getAllByRole('heading', { level: 4 });
    
    // Critical should come first, then high, then medium
    expect(gapTitles[0]).toHaveTextContent('Missing Packaging Supplier');
    expect(gapTitles[1]).toHaveTextContent('Pending Dye Confirmation');
    expect(gapTitles[2]).toHaveTextContent('Low Transparency Score');
  });

  it('displays gap type labels correctly', () => {
    render(<GapAnalysisPanel gaps={mockGaps} />);
    
    expect(screen.getByText('Missing Supplier')).toBeInTheDocument();
    expect(screen.getByText('Unconfirmed Order')).toBeInTheDocument();
    expect(screen.getByText('Low Transparency')).toBeInTheDocument();
  });

  it('shows impact scores and improvement estimates', () => {
    render(<GapAnalysisPanel gaps={mockGaps} />);
    
    expect(screen.getByText('Impact: 15.2')).toBeInTheDocument();
    expect(screen.getByText('Improvement: +8.5%')).toBeInTheDocument();
    expect(screen.getByText('1 nodes affected')).toBeInTheDocument();
  });

  it('handles showRecommendations prop', () => {
    render(<GapAnalysisPanel gaps={mockGaps} showRecommendations={false} />);
    
    // Expand gap
    fireEvent.click(screen.getByText('Missing Packaging Supplier'));
    
    // Recommendations should not be shown
    expect(screen.queryByText('Recommendations')).not.toBeInTheDocument();
  });
});

describe('GapAnalysisPanel accessibility', () => {
  it('has proper heading structure', () => {
    render(<GapAnalysisPanel gaps={mockGaps} />);
    
    expect(screen.getByRole('heading', { name: /Gap Analysis/ })).toBeInTheDocument();
  });

  it('provides keyboard navigation for gaps', () => {
    render(<GapAnalysisPanel gaps={mockGaps} />);
    
    const gapElements = screen.getAllByRole('button', { name: /Take Action/ });
    expect(gapElements.length).toBeGreaterThan(0);
  });

  it('has proper ARIA labels for interactive elements', () => {
    render(<GapAnalysisPanel gaps={mockGaps} />);
    
    // Filter buttons should be accessible
    const filterButtons = screen.getAllByRole('button');
    expect(filterButtons.length).toBeGreaterThan(0);
  });
});
