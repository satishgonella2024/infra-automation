import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import theme from '../theme';
import ArgoCD from '../pages/ArgoCD';
import { argoCDRequest } from '../services/api';

// Mock the API service
jest.mock('../services/api', () => ({
  argoCDRequest: jest.fn(),
}));

const renderWithTheme = (component) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('ArgoCD Component', () => {
  beforeEach(() => {
    // Clear mock calls before each test
    argoCDRequest.mockClear();
  });

  it('renders without crashing', () => {
    renderWithTheme(<ArgoCD />);
    expect(screen.getByText('ArgoCD Management')).toBeTruthy();
  });

  it('displays form fields for creating an application', () => {
    renderWithTheme(<ArgoCD />);
    
    // Select create_application action using combobox role
    const actionSelect = screen.getByRole('combobox');
    fireEvent.mouseDown(actionSelect);
    fireEvent.click(screen.getByText('Create Application'));

    // Check for form fields using role selectors
    expect(screen.getByRole('textbox', { name: /application name/i })).toBeTruthy();
    expect(screen.getByRole('textbox', { name: /project/i })).toBeTruthy();
    expect(screen.getByRole('textbox', { name: /repository url/i })).toBeTruthy();
    expect(screen.getByRole('textbox', { name: /path/i })).toBeTruthy();
    expect(screen.getByRole('textbox', { name: /target revision/i })).toBeTruthy();
    expect(screen.getByRole('textbox', { name: /namespace/i })).toBeTruthy();
  });

  it('handles application creation successfully', async () => {
    // Mock successful API response
    argoCDRequest.mockResolvedValueOnce({ 
      success: true,
      data: {
        name: 'test-app',
        project: 'default',
        namespace: 'default'
      }
    });

    renderWithTheme(<ArgoCD />);

    // Fill out form using role selectors
    fireEvent.change(screen.getByRole('textbox', { name: /application name/i }), {
      target: { value: 'test-app' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: /project/i }), {
      target: { value: 'default' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: /repository url/i }), {
      target: { value: 'https://github.com/org/repo' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: /path/i }), {
      target: { value: 'k8s' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: /target revision/i }), {
      target: { value: 'main' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: /namespace/i }), {
      target: { value: 'default' },
    });

    // Configure sync policy using role selectors
    fireEvent.click(screen.getByRole('checkbox', { name: /automated sync/i }));
    fireEvent.click(screen.getByRole('checkbox', { name: /prune resources/i }));
    fireEvent.click(screen.getByRole('checkbox', { name: /self heal/i }));

    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));

    // Wait for success message
    await waitFor(() => {
      expect(screen.queryByText('Operation completed successfully')).toBeTruthy();
    }, { timeout: 3000 });

    // Verify API was called with correct data
    expect(argoCDRequest).toHaveBeenCalledWith({
      action: 'create_application',
      parameters: expect.objectContaining({
        name: 'test-app',
        project: 'default',
        repoURL: 'https://github.com/org/repo',
        path: 'k8s',
        targetRevision: 'main',
        namespace: 'default',
        syncPolicy: {
          automated: true,
          prune: true,
          selfHeal: true
        }
      }),
    });
  });

  it('handles application sync', async () => {
    // Mock successful API response
    argoCDRequest.mockResolvedValueOnce({
      success: true,
      data: {
        name: 'test-app',
        status: 'Synced'
      }
    });

    renderWithTheme(<ArgoCD />);

    // Select sync_application action using combobox role
    const actionSelect = screen.getByRole('combobox');
    fireEvent.mouseDown(actionSelect);
    fireEvent.click(screen.getByText('Sync Application'));

    // Fill out form using role selectors
    fireEvent.change(screen.getByRole('textbox', { name: /application name/i }), {
      target: { value: 'test-app' },
    });
    fireEvent.click(screen.getByRole('checkbox', { name: /prune resources/i }));
    fireEvent.click(screen.getByRole('checkbox', { name: /dry run/i }));

    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));

    // Wait for success message
    await waitFor(() => {
      expect(screen.queryByText('Operation completed successfully')).toBeTruthy();
    }, { timeout: 3000 });

    // Verify API was called with correct data
    expect(argoCDRequest).toHaveBeenCalledWith({
      action: 'sync_application',
      parameters: expect.objectContaining({
        name: 'test-app',
        prune: true,
        dryRun: true
      }),
    });
  });

  it('handles API errors', async () => {
    // Mock API error
    argoCDRequest.mockRejectedValueOnce(new Error('API Error'));

    renderWithTheme(<ArgoCD />);

    // Fill out minimal form using role selectors
    fireEvent.change(screen.getByRole('textbox', { name: /application name/i }), {
      target: { value: 'test-app' },
    });

    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));

    // Wait for error message
    await waitFor(() => {
      expect(screen.queryByText('API Error')).toBeTruthy();
    }, { timeout: 3000 });
  });

  it('changes form fields based on selected action', () => {
    renderWithTheme(<ArgoCD />);

    // Change action to get_status using combobox role
    const actionSelect = screen.getByRole('combobox');
    fireEvent.mouseDown(actionSelect);
    fireEvent.click(screen.getByText('Get Application Status'));

    // Verify that only application name field is shown
    expect(screen.getByRole('textbox', { name: /application name/i })).toBeTruthy();
    expect(screen.queryByRole('textbox', { name: /repository url/i })).not.toBeInTheDocument();
  });

  it('displays application status section', () => {
    renderWithTheme(<ArgoCD />);

    // Verify status section elements are present
    expect(screen.getByText('Application Status')).toBeTruthy();
    expect(screen.getByText('frontend-app')).toBeTruthy();
    expect(screen.getByText('backend-api')).toBeTruthy();
    expect(screen.getByText('database')).toBeTruthy();
  });

  it('validates required fields', async () => {
    renderWithTheme(<ArgoCD />);

    // Try to submit empty form
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));

    // Check for HTML5 validation messages
    const appNameField = screen.getByRole('textbox', { name: /application name/i });
    const repoUrlField = screen.getByRole('textbox', { name: /repository url/i });
    
    expect(appNameField).toBeRequired();
    expect(repoUrlField).toBeRequired();
  });
}); 