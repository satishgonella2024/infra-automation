import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import { BrowserRouter } from 'react-router-dom';
import theme from '../theme';
import Dashboard from '../pages/Dashboard';
import { fetchTasks } from '../services/api';

// Mock the API service
jest.mock('../services/api', () => ({
  fetchTasks: jest.fn(),
}));

// Mock fetch for metrics
global.fetch = jest.fn();

const renderWithTheme = (component) => {
  return render(
    <BrowserRouter>
      <ThemeProvider theme={theme}>
        {component}
      </ThemeProvider>
    </BrowserRouter>
  );
};

describe('Dashboard Component', () => {
  const mockApiStatus = {
    status: 'online',
    version: '1.0.0',
    uptime_seconds: 3600,
    agents: [
      { name: 'Infrastructure', status: 'running' },
      { name: 'Security', status: 'idle' },
      { name: 'Kubernetes', status: 'running' },
      { name: 'ArgoCD', status: 'idle' }
    ]
  };

  beforeEach(() => {
    // Clear mock calls before each test
    fetchTasks.mockClear();
    global.fetch.mockClear();

    // Mock successful metrics response
    global.fetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        cpu_usage: 45,
        memory_usage: {
          percent: 60,
          used_gb: 8,
          total_gb: 16
        },
        disk_usage: {
          percent: 70,
          used: '80GB',
          total: '120GB'
        }
      })
    });
  });

  it('renders without crashing', () => {
    renderWithTheme(<Dashboard apiStatus={mockApiStatus} />);
    expect(screen.getByText('Dashboard')).toBeTruthy();
  });

  it('displays API status correctly', () => {
    renderWithTheme(<Dashboard apiStatus={mockApiStatus} />);
    expect(screen.getByText('API Status')).toBeTruthy();
    expect(screen.getByText('online')).toBeTruthy();
    expect(screen.getByText('System is operational')).toBeTruthy();
  });

  it('displays system information', () => {
    renderWithTheme(<Dashboard apiStatus={mockApiStatus} />);
    expect(screen.getByText('System Information')).toBeTruthy();
    expect(screen.getByText('Version: 1.0.0')).toBeTruthy();
    expect(screen.getByText('Uptime: 1 hours 0 minutes')).toBeTruthy();
  });

  it('displays agent status cards', () => {
    renderWithTheme(<Dashboard apiStatus={mockApiStatus} />);
    expect(screen.getByText('Agent Status')).toBeTruthy();
    expect(screen.getByText('Infrastructure')).toBeTruthy();
    expect(screen.getByText('Security')).toBeTruthy();
    expect(screen.getByText('Kubernetes')).toBeTruthy();
    expect(screen.getByText('ArgoCD')).toBeTruthy();
  });

  it('handles task loading and display', async () => {
    // Mock successful tasks response
    fetchTasks.mockResolvedValueOnce([
      {
        id: '1',
        task_type: 'infrastructure_generation',
        status: 'completed',
        description: 'Generate AWS Infrastructure',
        created_at: new Date().toISOString()
      },
      {
        id: '2',
        task_type: 'security_review',
        status: 'processing',
        description: 'Security Scan',
        created_at: new Date().toISOString()
      }
    ]);

    renderWithTheme(<Dashboard apiStatus={mockApiStatus} />);

    // Wait for tasks to load
    await waitFor(() => {
      expect(screen.getByText('Generate AWS Infrastructure')).toBeTruthy();
      expect(screen.getByText('Security Scan')).toBeTruthy();
    });
  });

  it('displays system metrics when available', async () => {
    renderWithTheme(<Dashboard apiStatus={mockApiStatus} />);

    await waitFor(() => {
      expect(screen.getByText('System Metrics')).toBeTruthy();
      expect(screen.getByText('45%')).toBeTruthy(); // CPU Usage
      expect(screen.getByText('60%')).toBeTruthy(); // Memory Usage
      expect(screen.getByText('70%')).toBeTruthy(); // Disk Usage
    });
  });

  it('handles refresh button click', async () => {
    fetchTasks.mockResolvedValueOnce([]);
    renderWithTheme(<Dashboard apiStatus={mockApiStatus} />);

    // Click refresh button
    fireEvent.click(screen.getByText('Refresh'));

    // Verify that fetchTasks was called
    await waitFor(() => {
      expect(fetchTasks).toHaveBeenCalledTimes(2); // Once on mount, once on click
    });
  });

  it('displays error state for failed metrics fetch', async () => {
    // Mock failed metrics response
    global.fetch.mockRejectedValueOnce(new Error('Failed to fetch metrics'));

    renderWithTheme(<Dashboard apiStatus={mockApiStatus} />);

    await waitFor(() => {
      expect(screen.getByText('Error loading metrics: Failed to fetch metrics')).toBeTruthy();
    });
  });

  it('displays quick action cards', () => {
    renderWithTheme(<Dashboard apiStatus={mockApiStatus} />);
    
    expect(screen.getByText('Generate Infrastructure')).toBeTruthy();
    expect(screen.getByText('Security Review')).toBeTruthy();
    expect(screen.getByText('Visualize')).toBeTruthy();
    expect(screen.getByText('Task History')).toBeTruthy();
  });

  it('handles empty task list', async () => {
    fetchTasks.mockResolvedValueOnce([]);
    renderWithTheme(<Dashboard apiStatus={mockApiStatus} />);

    await waitFor(() => {
      expect(screen.getByText('No recent tasks found')).toBeTruthy();
    });
  });
}); 