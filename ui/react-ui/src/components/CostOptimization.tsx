interface CostAnalysisResponse {
  task_id: string;
  original_code: string;
  optimized_code: string;
  cost_analysis: {
    optimization_opportunities: Array<{
      description: string;
      potential_savings: number;
      priority: string;
    }>;
    // ... other cost analysis fields
  };
  optimization_summary: {
    total_savings: number;
    recommendations: string[];
  };
  thoughts: string;
  cloud_provider: string;
  iac_type: string;
}

const CostOptimization: React.FC = () => {
  // ... existing code ...

  return (
    <div>
      {/* ... existing code ... */}
      {response && response.cost_analysis && response.cost_analysis.optimization_opportunities && (
        <div>
          <h3>Optimization Opportunities</h3>
          {response.cost_analysis.optimization_opportunities.map((opportunity, index) => (
            <div key={index}>
              <p>{opportunity.description}</p>
              <p>Potential Savings: ${opportunity.potential_savings}</p>
              <p>Priority: {opportunity.priority}</p>
            </div>
          ))}
        </div>
      )}
      {/* ... existing code ... */}
    </div>
  );
}; 