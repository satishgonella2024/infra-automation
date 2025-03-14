import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import theme from '../theme';
import Kubernetes from '../pages/Kubernetes';
import { kubernetesRequest } from '../services/api';

// Mock the API service
jest.mock('../services/api', () => ({
  kubernetesRequest: jest.fn(),
}));

const renderWithTheme = (component) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('Kubernetes Component', () => {
  beforeEach(() => {
    // Clear mock calls before each test
    kubernetesRequest.mockClear();
  });

  it('renders without crashing', () => {
    renderWithTheme(<Kubernetes />);
    expect(screen.getByText('Kubernetes Management')).toBeTruthy();
  });

  it('displays deployment form fields', () => {
    renderWithTheme(<Kubernetes />);
    
    // Deployment tab should be active by default
    expect(screen.getByRole('textbox', { name: /application name/i })).toBeTruthy();
    expect(screen.getByRole('textbox', { name: /namespace/i })).toBeTruthy();
    expect(screen.getByRole('textbox', { name: /replicas/i })).toBeTruthy();
    expect(screen.getByRole('textbox', { name: /container image/i })).toBeTruthy();
    expect(screen.getByRole('textbox', { name: /container port/i })).toBeTruthy();
    expect(screen.getByRole('textbox', { name: /cpu limit/i })).toBeTruthy();
    expect(screen.getByRole('textbox', { name: /memory limit/i })).toBeTruthy();
  });

  it('handles deployment creation successfully', async () => {
    // Mock successful API response
    kubernetesRequest.mockResolvedValueOnce({ 
      success: true,
      data: {
        name: 'test-app',
        namespace: 'default',
        replicas: 3
      }
    });

    renderWithTheme(<Kubernetes />);

    // Fill out deployment form using role selectors
    fireEvent.change(screen.getByRole('textbox', { name: /application name/i }), {
      target: { value: 'test-app' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: /namespace/i }), {
      target: { value: 'default' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: /replicas/i }), {
      target: { value: '3' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: /container image/i }), {
      target: { value: 'nginx:latest' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: /container port/i }), {
      target: { value: '80' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: /cpu limit/i }), {
      target: { value: '500m' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: /memory limit/i }), {
      target: { value: '512Mi' },
    });

    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /generate manifests/i }));

    // Wait for success message
    await waitFor(() => {
      expect(screen.getByText('Operation completed successfully')).toBeTruthy();
    });

    // Verify API was called with correct data
    expect(kubernetesRequest).toHaveBeenCalledWith({
      action: 'generate_manifests',
      parameters: expect.objectContaining({
        name: 'test-app',
        namespace: 'default',
        replicas: 3,
        image: 'nginx:latest',
        containerPort: 80,
        resourceLimits: {
          cpu: '500m',
          memory: '512Mi'
        }
      }),
    });
  });

  it('switches to analysis tab and displays analysis form', () => {
    renderWithTheme(<Kubernetes />);

    // Click on Analysis tab
    fireEvent.click(screen.getByRole('tab', { name: /analysis/i }));

    // Verify analysis form fields are shown
    expect(screen.getByRole('textbox', { name: /namespace/i })).toBeTruthy();
    expect(screen.getByRole('button', { name: /analysis type/i })).toBeTruthy();
  });

  it('handles resource analysis successfully', async () => {
    // Mock successful API response
    kubernetesRequest.mockResolvedValueOnce({
      success: true,
      data: {
        namespace: 'default',
        analysisType: 'security',
        findings: []
      }
    });

    renderWithTheme(<Kubernetes />);

    // Switch to Analysis tab
    fireEvent.click(screen.getByRole('tab', { name: /analysis/i }));

    // Fill out analysis form using role selectors
    fireEvent.change(screen.getByRole('textbox', { name: /namespace/i }), {
      target: { value: 'default' },
    });
    
    // Select analysis type
    const analysisTypeSelect = screen.getByRole('button', { name: /analysis type/i });
    fireEvent.mouseDown(analysisTypeSelect);
    fireEvent.click(screen.getByText('Security Analysis'));

    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /run analysis/i }));

    // Wait for success message
    await waitFor(() => {
      expect(screen.getByText('Operation completed successfully')).toBeTruthy();
    });

    // Verify API was called with correct data
    expect(kubernetesRequest).toHaveBeenCalledWith({
      action: 'analyze_resources',
      parameters: expect.objectContaining({
        namespace: 'default',
        analysisType: 'security'
      }),
    });
  });

  it('handles API errors', async () => {
    // Mock API error
    kubernetesRequest.mockRejectedValueOnce(new Error('API Error'));

    renderWithTheme(<Kubernetes />);

    // Fill out minimal form using role selectors
    fireEvent.change(screen.getByRole('textbox', { name: /application name/i }), {
      target: { value: 'test-app' },
    });

    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /generate manifests/i }));

    // Wait for error message
    await waitFor(() => {
      expect(screen.getByText('API Error')).toBeTruthy();
    });
  });

  it('validates required fields', async () => {
    renderWithTheme(<Kubernetes />);

    // Try to submit empty form
    fireEvent.click(screen.getByRole('button', { name: /generate manifests/i }));

    // Check for HTML5 validation messages
    const appNameField = screen.getByRole('textbox', { name: /application name/i });
    const containerImageField = screen.getByRole('textbox', { name: /container image/i });
    
    expect(appNameField).toBeRequired();
    expect(containerImageField).toBeRequired();
  });

  it('displays cluster overview section', () => {
    renderWithTheme(<Kubernetes />);

    // Verify cluster overview elements are present
    expect(screen.getByText('Cluster Overview')).toBeTruthy();
    expect(screen.getByText('Active Deployments')).toBeTruthy();
    expect(screen.getByText('Resource Usage')).toBeTruthy();
    expect(screen.getByText('Network Status')).toBeTruthy();
  });
}); 