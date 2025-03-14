import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import theme from '../theme';
import Nexus from '../pages/Nexus';
import { nexusRequest } from '../services/api';

// Mock the API service
jest.mock('../services/api', () => ({
  nexusRequest: jest.fn(),
}));

const renderWithTheme = (component) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('Nexus Component', () => {
  beforeEach(() => {
    // Clear mock calls before each test
    nexusRequest.mockClear();
  });

  it('renders without crashing', () => {
    renderWithTheme(<Nexus />);
    expect(screen.getByText('Nexus Repository Manager')).toBeTruthy();
  });

  it('displays form fields for creating a repository', () => {
    renderWithTheme(<Nexus />);
    
    // Select create_repository action using role selectors
    const actionSelect = screen.getByRole('button', { name: /action/i });
    fireEvent.mouseDown(actionSelect);
    fireEvent.click(screen.getByText('Create Repository'));

    // Check for form fields using role selectors
    expect(screen.getByRole('textbox', { name: /repository name/i })).toBeTruthy();
    expect(screen.getByRole('button', { name: /format/i })).toBeTruthy();
    expect(screen.getByRole('button', { name: /type/i })).toBeTruthy();
    expect(screen.getByRole('textbox', { name: /description/i })).toBeTruthy();
  });

  it('handles repository creation successfully', async () => {
    // Mock successful API response
    nexusRequest.mockResolvedValueOnce({ 
      success: true,
      data: {
        name: 'test-repo',
        format: 'maven2',
        type: 'hosted'
      }
    });

    renderWithTheme(<Nexus />);

    // Fill out form using role selectors
    fireEvent.change(screen.getByRole('textbox', { name: /repository name/i }), {
      target: { value: 'test-repo' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: /description/i }), {
      target: { value: 'Test repository' },
    });

    // Select format
    const formatSelect = screen.getByRole('button', { name: /format/i });
    fireEvent.mouseDown(formatSelect);
    fireEvent.click(screen.getByText('Maven2'));

    // Select type
    const typeSelect = screen.getByRole('button', { name: /type/i });
    fireEvent.mouseDown(typeSelect);
    fireEvent.click(screen.getByText('Hosted'));

    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));

    // Wait for success message
    await waitFor(() => {
      expect(screen.getByText('Operation completed successfully')).toBeTruthy();
    });

    // Verify API was called with correct data
    expect(nexusRequest).toHaveBeenCalledWith({
      action: 'create_repository',
      parameters: expect.objectContaining({
        name: 'test-repo',
        format: 'maven2',
        type: 'hosted',
        description: 'Test repository',
      }),
    });
  });

  it('handles artifact upload', async () => {
    // Mock successful API response
    nexusRequest.mockResolvedValueOnce({
      success: true,
      data: {
        repository: 'test-repo',
        group_id: 'com.example',
        artifact_id: 'test-artifact',
        version: '1.0.0'
      }
    });

    renderWithTheme(<Nexus />);

    // Select upload_artifact action using role selectors
    const actionSelect = screen.getByRole('combobox', { name: /action/i });
    fireEvent.mouseDown(actionSelect);
    fireEvent.click(screen.getByText('Upload Artifact'));

    // Fill out form using role selectors
    fireEvent.change(screen.getByRole('textbox', { name: /repository/i }), {
      target: { value: 'test-repo' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: /group id/i }), {
      target: { value: 'com.example' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: /artifact id/i }), {
      target: { value: 'test-artifact' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: /version/i }), {
      target: { value: '1.0.0' },
    });

    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));

    // Wait for success message
    await waitFor(() => {
      expect(screen.getByText('Operation completed successfully')).toBeTruthy();
    });

    // Verify API was called with correct data
    expect(nexusRequest).toHaveBeenCalledWith({
      action: 'upload_artifact',
      parameters: expect.objectContaining({
        repository: 'test-repo',
        group_id: 'com.example',
        artifact_id: 'test-artifact',
        version: '1.0.0'
      }),
    });
  });

  it('handles API errors', async () => {
    // Mock API error
    nexusRequest.mockRejectedValueOnce(new Error('API Error'));

    renderWithTheme(<Nexus />);

    // Fill out form using role selectors
    fireEvent.change(screen.getByRole('textbox', { name: /repository name/i }), {
      target: { value: 'test-repo' },
    });

    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));

    // Wait for error message
    await waitFor(() => {
      expect(screen.queryByText('API Error')).toBeTruthy();
    });
  });

  it('changes form fields based on selected action', () => {
    renderWithTheme(<Nexus />);

    // Change action to search_artifacts using role selectors
    const actionSelect = screen.getByRole('combobox', { name: /action/i });
    fireEvent.mouseDown(actionSelect);
    fireEvent.click(screen.getByText('Search Artifacts'));

    // Verify that repository name field is shown
    expect(screen.getByRole('textbox', { name: /repository/i })).toBeTruthy();
    // Verify that search query field is shown
    expect(screen.getByRole('textbox', { name: /search query/i })).toBeTruthy();
    // Verify that format field is not shown
    expect(screen.queryByRole('button', { name: /format/i })).not.toBeInTheDocument();
  });

  it('handles cleanup policy creation', async () => {
    // Mock successful API response
    nexusRequest.mockResolvedValueOnce({
      success: true,
      data: {
        name: 'test-policy',
        format: 'maven2'
      }
    });

    renderWithTheme(<Nexus />);

    // Select create_cleanup_policy action using role selectors
    const actionSelect = screen.getByRole('combobox', { name: /action/i });
    fireEvent.mouseDown(actionSelect);
    fireEvent.click(screen.getByText('Create Cleanup Policy'));

    // Fill out form using role selectors
    fireEvent.change(screen.getByRole('textbox', { name: /cleanup policy/i }), {
      target: { value: 'test-policy' },
    });

    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));

    // Wait for success message
    await waitFor(() => {
      expect(screen.getByText('Operation completed successfully')).toBeTruthy();
    });

    // Verify API was called with correct data
    expect(nexusRequest).toHaveBeenCalledWith({
      action: 'create_cleanup_policy',
      parameters: expect.objectContaining({
        cleanup_policy: 'test-policy'
      }),
    });
  });
}); 