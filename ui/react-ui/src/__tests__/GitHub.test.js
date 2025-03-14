import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import theme from '../theme';
import GitHub from '../pages/GitHub';
import { githubRequest } from '../services/api';

// Mock the API service
jest.mock('../services/api', () => ({
  githubRequest: jest.fn(),
}));

const renderWithTheme = (component) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('GitHub Component', () => {
  beforeEach(() => {
    // Clear mock calls before each test
    githubRequest.mockClear();
  });

  it('renders without crashing', () => {
    renderWithTheme(<GitHub />);
    expect(screen.getByText('GitHub Integration')).toBeTruthy();
  });

  it('displays form fields for creating a repository', () => {
    renderWithTheme(<GitHub />);
    
    // Select create_repository action
    const actionSelect = screen.getByRole('button', { name: /action/i });
    fireEvent.mouseDown(actionSelect);
    fireEvent.click(screen.getByText('Create Repository'));

    expect(screen.getByRole('textbox', { name: /repository name/i })).toBeTruthy();
    expect(screen.getByRole('textbox', { name: /description/i })).toBeTruthy();
    expect(screen.getByRole('checkbox', { name: /private/i })).toBeTruthy();
  });

  it('handles repository creation successfully', async () => {
    // Mock successful API response
    githubRequest.mockResolvedValueOnce({ 
      success: true,
      data: {
        name: 'test-repo',
        html_url: 'https://github.com/org/test-repo'
      }
    });

    renderWithTheme(<GitHub />);

    // Select create_repository action
    const actionSelect = screen.getByRole('button', { name: /action/i });
    fireEvent.mouseDown(actionSelect);
    fireEvent.click(screen.getByText('Create Repository'));

    // Fill out form
    fireEvent.change(screen.getByRole('textbox', { name: /repository name/i }), {
      target: { value: 'test-repo' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: /description/i }), {
      target: { value: 'Test repository' },
    });
    fireEvent.click(screen.getByRole('checkbox', { name: /private/i }));

    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));

    // Wait for success message
    await waitFor(() => {
      expect(screen.getByText('Operation completed successfully')).toBeTruthy();
    });

    // Verify API was called with correct data
    expect(githubRequest).toHaveBeenCalledWith({
      action: 'create_repository',
      parameters: expect.objectContaining({
        name: 'test-repo',
        description: 'Test repository',
        private: true,
      }),
    });
  });

  it('handles pull request creation', async () => {
    // Mock successful API response
    githubRequest.mockResolvedValueOnce({
      success: true,
      data: {
        number: 1,
        html_url: 'https://github.com/org/repo/pull/1'
      }
    });

    renderWithTheme(<GitHub />);

    // Select create_pull_request action
    const actionSelect = screen.getByRole('button', { name: /action/i });
    fireEvent.mouseDown(actionSelect);
    fireEvent.click(screen.getByText('Create Pull Request'));

    // Fill out form
    fireEvent.change(screen.getByRole('textbox', { name: /repository/i }), {
      target: { value: 'test-repo' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: /title/i }), {
      target: { value: 'Test PR' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: /base branch/i }), {
      target: { value: 'main' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: /head branch/i }), {
      target: { value: 'feature' },
    });

    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));

    // Wait for success message
    await waitFor(() => {
      expect(screen.getByText('Operation completed successfully')).toBeTruthy();
    });

    // Verify API was called with correct data
    expect(githubRequest).toHaveBeenCalledWith({
      action: 'create_pull_request',
      parameters: expect.objectContaining({
        repository: 'test-repo',
        title: 'Test PR',
        base: 'main',
        head: 'feature',
      }),
    });
  });

  it('handles API errors', async () => {
    // Mock API error
    githubRequest.mockRejectedValueOnce(new Error('API Error'));

    renderWithTheme(<GitHub />);

    // Select create_repository action
    const actionSelect = screen.getByRole('button', { name: /action/i });
    fireEvent.mouseDown(actionSelect);
    fireEvent.click(screen.getByText('Create Repository'));

    // Fill out form
    fireEvent.change(screen.getByRole('textbox', { name: /repository name/i }), {
      target: { value: 'test-repo' },
    });

    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));

    // Wait for error message
    await waitFor(() => {
      expect(screen.getByText('API Error')).toBeTruthy();
    });
  });

  it('changes form fields based on selected action', () => {
    renderWithTheme(<GitHub />);

    // Change action to review_code
    const actionSelect = screen.getByRole('button', { name: /action/i });
    fireEvent.mouseDown(actionSelect);
    fireEvent.click(screen.getByText('Review Code'));

    // Verify that repository field is shown
    expect(screen.getByRole('textbox', { name: /repository/i })).toBeTruthy();
    // Verify that pull request number field is shown
    expect(screen.getByRole('textbox', { name: /pull request number/i })).toBeTruthy();
  });
}); 