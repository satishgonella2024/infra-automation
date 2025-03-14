import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import theme from '../theme';
import Jira from '../pages/Jira';
import { jiraRequest } from '../services/api';

// Mock the API service
jest.mock('../services/api', () => ({
  jiraRequest: jest.fn(),
}));

const renderWithTheme = (component) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('Jira Component', () => {
  beforeEach(() => {
    // Clear mock calls before each test
    jiraRequest.mockClear();
  });

  it('renders without crashing', () => {
    renderWithTheme(<Jira />);
    expect(screen.getByText('Jira Integration')).toBeTruthy();
  });

  it('displays form fields for creating an issue', () => {
    renderWithTheme(<Jira />);
    
    // Find form fields by their role and name
    expect(screen.getByRole('textbox', { name: /project/i })).toBeTruthy();
    expect(screen.getByRole('textbox', { name: /summary/i })).toBeTruthy();
    expect(screen.getByRole('textbox', { name: /description/i })).toBeTruthy();
  });

  it('handles form submission successfully', async () => {
    // Mock successful API response
    jiraRequest.mockResolvedValueOnce({ 
      success: true,
      data: {
        key: 'TEST-123',
        summary: 'Test Issue'
      }
    });

    renderWithTheme(<Jira />);

    // Fill out form using role selectors
    fireEvent.change(screen.getByRole('textbox', { name: /project/i }), {
      target: { value: 'TEST' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: /summary/i }), {
      target: { value: 'Test Issue' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: /description/i }), {
      target: { value: 'Test Description' },
    });

    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));

    // Wait for success message
    await waitFor(() => {
      expect(screen.getByText('Operation completed successfully')).toBeTruthy();
    });

    // Verify API was called with correct data
    expect(jiraRequest).toHaveBeenCalledWith({
      action: 'create_issue',
      parameters: {
        project: 'TEST',
        summary: 'Test Issue',
        description: 'Test Description'
      }
    });
  });

  it('handles API errors', async () => {
    // Mock API error
    jiraRequest.mockRejectedValueOnce(new Error('API Error'));

    renderWithTheme(<Jira />);

    // Fill out form using role selectors
    fireEvent.change(screen.getByRole('textbox', { name: /project/i }), {
      target: { value: 'TEST' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: /summary/i }), {
      target: { value: 'Test Issue' },
    });

    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));

    // Wait for error message
    await waitFor(() => {
      expect(screen.getByText('API Error')).toBeTruthy();
    });
  });

  it('changes form fields based on selected action', () => {
    renderWithTheme(<Jira />);

    // Find and click the action select
    const actionSelect = screen.getByRole('button', { name: /action/i });
    fireEvent.mouseDown(actionSelect);
    
    // Select "Search Issues" from the dropdown
    const searchOption = screen.getByRole('option', { name: /search issues/i });
    fireEvent.click(searchOption);

    // Verify that summary and description fields are not shown
    expect(screen.queryByRole('textbox', { name: /summary/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('textbox', { name: /description/i })).not.toBeInTheDocument();
    
    // Verify that search fields are shown
    expect(screen.getByRole('textbox', { name: /search query/i })).toBeTruthy();
  });
}); 