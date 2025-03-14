import React from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import theme from '../theme';
import AgentStatus from '../components/AgentStatus';

const renderWithTheme = (component) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('AgentStatus Component', () => {
  const mockAgents = [
    {
      name: 'Infrastructure',
      status: 'running',
      description: 'Generates infrastructure as code',
      last_active_time: Math.floor(Date.now() / 1000)
    },
    {
      name: 'Security',
      status: 'idle',
      description: 'Analyzes infrastructure for security vulnerabilities',
      last_active_time: Math.floor(Date.now() / 1000)
    },
    {
      name: 'Kubernetes',
      status: 'error',
      description: 'Manages Kubernetes resources',
      last_active_time: Math.floor(Date.now() / 1000)
    },
    {
      name: 'ArgoCD',
      status: 'degraded',
      description: 'Manages GitOps deployments',
      last_active_time: Math.floor(Date.now() / 1000)
    }
  ];

  it('renders without crashing', () => {
    renderWithTheme(<AgentStatus agents={mockAgents} />);
    expect(screen.getByText('Agent Status')).toBeInTheDocument();
  });

  it('displays all agent cards', () => {
    renderWithTheme(<AgentStatus agents={mockAgents} />);
    mockAgents.forEach(agent => {
      expect(screen.getByText(agent.name)).toBeInTheDocument();
      expect(screen.getByText(agent.status)).toBeInTheDocument();
    });
  });

  it('handles empty agents array', () => {
    renderWithTheme(<AgentStatus agents={[]} />);
    expect(screen.getByText('Agent Status')).toBeInTheDocument();
  });

  it('displays correct status colors', () => {
    renderWithTheme(<AgentStatus agents={mockAgents} />);
    
    // Find status chips by their text content
    const runningStatus = screen.getByText('running').closest('.MuiChip-root');
    const idleStatus = screen.getByText('idle').closest('.MuiChip-root');
    const errorStatus = screen.getByText('error').closest('.MuiChip-root');
    const degradedStatus = screen.getByText('degraded').closest('.MuiChip-root');

    // Check color classes
    expect(runningStatus).toHaveClass('MuiChip-colorSuccess');
    expect(idleStatus).toHaveClass('MuiChip-colorSuccess');
    expect(errorStatus).toHaveClass('MuiChip-colorError');
    expect(degradedStatus).toHaveClass('MuiChip-colorWarning');
  });

  it('displays agent descriptions in tooltips', () => {
    renderWithTheme(<AgentStatus agents={mockAgents} />);
    mockAgents.forEach(agent => {
      const tooltip = screen.getByText(agent.description);
      expect(tooltip).toBeInTheDocument();
    });
  });

  it('displays last active time for each agent', () => {
    renderWithTheme(<AgentStatus agents={mockAgents} />);
    mockAgents.forEach(agent => {
      const time = new Date(agent.last_active_time * 1000).toLocaleTimeString();
      expect(screen.getByText(time)).toBeInTheDocument();
    });
  });

  it('handles agents passed as an object', () => {
    const agentsObject = {
      infrastructure: {
        status: 'running',
        last_active: Math.floor(Date.now() / 1000)
      },
      security: {
        status: 'idle',
        last_active: Math.floor(Date.now() / 1000)
      }
    };

    renderWithTheme(<AgentStatus agents={agentsObject} />);
    expect(screen.getByText('Infrastructure')).toBeInTheDocument();
    expect(screen.getByText('Security')).toBeInTheDocument();
  });

  it('displays appropriate icons for each agent type', () => {
    renderWithTheme(<AgentStatus agents={mockAgents} />);
    
    // The icons themselves are SVG elements, so we check their parent containers
    const agentCards = screen.getAllByRole('article');
    expect(agentCards).toHaveLength(mockAgents.length);
    
    // Each card should have an icon
    agentCards.forEach(card => {
      expect(card.querySelector('svg')).toBeInTheDocument();
    });
  });
}); 