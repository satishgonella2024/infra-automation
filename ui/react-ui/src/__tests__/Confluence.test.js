import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import theme from '../theme';
import Confluence from '../pages/Confluence';
import { confluenceRequest } from '../services/api';

// Mock the API service
jest.mock('../services/api', () => ({
  confluenceRequest: jest.fn(),
}));

const renderWithTheme = (component) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('Confluence Component', () => {
  beforeEach(() => {
    // Clear mock calls before each test
    confluenceRequest.mockClear();
  });

  it('renders without crashing', () => {
    renderWithTheme(<Confluence />);
    expect(screen.getByText('Confluence Integration')).toBeTruthy();
  });

  it('displays form fields for creating a page', () => {
    renderWithTheme(<Confluence />);
    
    // Check for form fields using role selectors
    expect(screen.getByRole('textbox', { name: /space key/i })).toBeTruthy();
    expect(screen.getByRole('textbox', { name: /title/i })).toBeTruthy();
    expect(screen.getByRole('textbox', { name: /content/i })).toBeTruthy();
  });

  it('handles form submission successfully', async () => {
    // Mock successful API response
    confluenceRequest.mockResolvedValueOnce({ 
      success: true,
      data: {
        id: '12345',
        title: 'Test Page'
      }
    });

    renderWithTheme(<Confluence />);

    // Fill out form using role selectors
    fireEvent.change(screen.getByRole('textbox', { name: /space key/i }), {
      target: { value: 'TEST' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: /title/i }), {
      target: { value: 'Test Page' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: /content/i }), {
      target: { value: 'Test Content' },
    });
    
    // Add labels
    fireEvent.change(screen.getByRole('textbox', { name: /labels/i }), {
      target: { value: 'label1,label2,label3' },
    });

    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));

    // Wait for success message
    await waitFor(() => {
      expect(screen.getByText('Operation completed successfully')).toBeTruthy();
    });

    // Verify API was called with correct data
    expect(confluenceRequest).toHaveBeenCalledWith(
      expect.objectContaining({
        parameters: expect.objectContaining({
          labels: ['label1', 'label2', 'label3'],
        }),
      })
    );
  });

  it('handles API errors', async () => {
    // Mock API error
    confluenceRequest.mockRejectedValueOnce(new Error('API Error'));

    renderWithTheme(<Confluence />);

    // Fill out form using role selectors
    fireEvent.change(screen.getByRole('textbox', { name: /space key/i }), {
      target: { value: 'TEST' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: /title/i }), {
      target: { value: 'Test Page' },
    });

    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));

    // Wait for error message
    await waitFor(() => {
      expect(screen.getByText('API Error')).toBeTruthy();
    });
  });

  it('changes form fields based on selected action', () => {
    renderWithTheme(<Confluence />);

    // Change action to generate_documentation using role selectors
    const actionSelect = screen.getByRole('button', { name: /action/i });
    fireEvent.mouseDown(actionSelect);
    fireEvent.click(screen.getByText('Generate Documentation'));

    // Verify that space key field is not shown
    expect(screen.queryByRole('textbox', { name: /space key/i })).not.toBeInTheDocument();
    
    // Verify that template field is shown
    expect(screen.getByRole('textbox', { name: /template/i })).toBeTruthy();
  });

  it('handles labels input correctly', async () => {
    // Mock successful API response
    confluenceRequest.mockResolvedValueOnce({ 
      success: true,
      data: {
        id: '12345',
        title: 'Test Page',
        labels: ['label1', 'label2', 'label3']
      }
    });

    renderWithTheme(<Confluence />);

    // Fill out form using role selectors
    fireEvent.change(screen.getByRole('textbox', { name: /space key/i }), {
      target: { value: 'TEST' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: /title/i }), {
      target: { value: 'Test Page' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: /content/i }), {
      target: { value: 'Test Content' },
    });
    
    // Add labels
    fireEvent.change(screen.getByRole('textbox', { name: /labels/i }), {
      target: { value: 'label1,label2,label3' },
    });

    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));

    // Wait for success message
    await waitFor(() => {
      expect(screen.getByText('Operation completed successfully')).toBeTruthy();
    });

    // Verify API was called with correct data
    expect(confluenceRequest).toHaveBeenCalledWith(
      expect.objectContaining({
        parameters: expect.objectContaining({
          labels: ['label1', 'label2', 'label3'],
        }),
      })
    );
  });
}); 