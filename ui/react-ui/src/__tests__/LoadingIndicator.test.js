import React from 'react';
import { render, screen, act } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import theme from '../theme';
import LoadingIndicator from '../components/LoadingIndicator';

const renderWithTheme = (component) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('LoadingIndicator Component', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('renders without crashing', () => {
    renderWithTheme(<LoadingIndicator />);
    expect(screen.getByText('Loading...')).toBeTruthy();
  });

  it('displays custom message', () => {
    const customMessage = 'Custom loading message';
    renderWithTheme(<LoadingIndicator message={customMessage} />);
    expect(screen.getByText(customMessage)).toBeTruthy();
  });

  it('shows progress bar when showProgress is true', () => {
    const { container } = renderWithTheme(<LoadingIndicator showProgress={true} />);
    // Use container query instead of role to avoid multiple elements issue
    const progressBar = container.querySelector('.MuiLinearProgress-root');
    expect(progressBar).toBeTruthy();
    expect(screen.getByText('0%')).toBeTruthy();
    expect(screen.getByText('100%')).toBeTruthy();
  });

  it('updates message after 10 seconds', () => {
    renderWithTheme(<LoadingIndicator />);
    
    // Fast-forward 10 seconds
    act(() => {
      jest.advanceTimersByTime(10000);
    });

    expect(screen.getByText('Still working...')).toBeTruthy();
  });

  it('updates message after 20 seconds', () => {
    renderWithTheme(<LoadingIndicator />);
    
    // Fast-forward 20 seconds
    act(() => {
      jest.advanceTimersByTime(20000);
    });

    expect(screen.getByText('This is taking longer than expected...')).toBeTruthy();
  });

  it('updates message after 30 seconds', () => {
    renderWithTheme(<LoadingIndicator />);
    
    // Fast-forward 30 seconds
    act(() => {
      jest.advanceTimersByTime(30000);
    });

    expect(screen.getByText('Almost there...')).toBeTruthy();
  });

  it('updates message after 60 seconds', () => {
    renderWithTheme(<LoadingIndicator />);
    
    // Fast-forward 60 seconds
    act(() => {
      jest.advanceTimersByTime(60000);
    });

    expect(screen.getByText('Processing complex request...')).toBeTruthy();
  });

  it('shows timeout warning after 240 seconds', () => {
    renderWithTheme(<LoadingIndicator />);
    
    // Fast-forward 240 seconds
    act(() => {
      jest.advanceTimersByTime(240000);
    });

    expect(screen.getByText("We're working hard on your request...")).toBeTruthy();
    expect(screen.getByText(/This request is taking longer than expected/)).toBeTruthy();
  });

  it('displays elapsed time correctly', () => {
    renderWithTheme(<LoadingIndicator />);
    
    // Fast-forward 65 seconds
    act(() => {
      jest.advanceTimersByTime(65000);
    });

    expect(screen.getByText('Time elapsed: 1:05')).toBeTruthy();
  });

  it('updates progress percentage based on timeout', () => {
    const { container } = renderWithTheme(<LoadingIndicator showProgress={true} timeout={30} />);
    
    // Fast-forward 15 seconds (50% of timeout)
    act(() => {
      jest.advanceTimersByTime(15000);
    });

    const progressBar = container.querySelector('.MuiLinearProgress-root');
    expect(progressBar).toHaveAttribute('aria-valuenow', '50');
  });

  it('caps progress at 90%', () => {
    const { container } = renderWithTheme(<LoadingIndicator showProgress={true} timeout={30} />);
    
    // Fast-forward 60 seconds (200% of timeout)
    act(() => {
      jest.advanceTimersByTime(60000);
    });

    const progressBar = container.querySelector('.MuiLinearProgress-root');
    expect(progressBar).toHaveAttribute('aria-valuenow', '90');
  });

  it('cleans up interval on unmount', () => {
    const { unmount } = renderWithTheme(<LoadingIndicator />);
    
    // Create a spy on clearInterval
    const clearIntervalSpy = jest.spyOn(window, 'clearInterval');
    
    // Unmount the component
    unmount();
    
    // Check if clearInterval was called
    expect(clearIntervalSpy).toHaveBeenCalled();
    
    clearIntervalSpy.mockRestore();
  });
}); 