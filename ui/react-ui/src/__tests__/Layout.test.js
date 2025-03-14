import React from 'react';
import { render, screen, fireEvent, within } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import theme from '../theme';
import Layout from '../components/Layout';

const renderWithTheme = (component) => {
  return render(
    <BrowserRouter>
      <ThemeProvider theme={theme}>
        {component}
      </ThemeProvider>
    </BrowserRouter>
  );
};

describe('Layout Component', () => {
  const mockApiStatus = {
    status: 'online',
    version: '1.0.0',
    agents: [
      { name: 'Infrastructure', status: 'running' },
      { name: 'Security', status: 'idle' }
    ]
  };

  const mockChildren = <div>Test Content</div>;

  it('renders without crashing', () => {
    renderWithTheme(
      <Layout apiStatus={mockApiStatus}>
        {mockChildren}
      </Layout>
    );
    expect(screen.getByText('Infra Automation')).toBeInTheDocument();
  });

  it('displays navigation categories', () => {
    renderWithTheme(
      <Layout apiStatus={mockApiStatus}>
        {mockChildren}
      </Layout>
    );

    const categories = ['Overview', 'Development', 'DevOps', 'Monitoring', 'Settings'];
    categories.forEach(category => {
      expect(screen.getByText(category)).toBeInTheDocument();
    });
  });

  it('displays all navigation items', () => {
    renderWithTheme(
      <Layout apiStatus={mockApiStatus}>
        {mockChildren}
      </Layout>
    );

    const navItems = [
      'Dashboard',
      'Infrastructure',
      'Security',
      'Cost',
      'Jira',
      'Confluence',
      'GitHub',
      'Nexus',
      'Kubernetes',
      'ArgoCD',
      'Observability',
      'Analytics',
      'History',
      'Settings'
    ];

    navItems.forEach(item => {
      expect(screen.getByText(item)).toBeInTheDocument();
    });
  });

  it('displays system status section', () => {
    renderWithTheme(
      <Layout apiStatus={mockApiStatus}>
        {mockChildren}
      </Layout>
    );

    expect(screen.getByText('System Status')).toBeInTheDocument();
    expect(screen.getByText('API: online')).toBeInTheDocument();
    mockApiStatus.agents.forEach(agent => {
      expect(screen.getByText(`${agent.name}: ${agent.status}`)).toBeInTheDocument();
    });
  });

  it('renders children content', () => {
    renderWithTheme(
      <Layout apiStatus={mockApiStatus}>
        {mockChildren}
      </Layout>
    );

    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  it('handles mobile menu toggle', () => {
    // Mock window.innerWidth
    global.innerWidth = 500;
    global.dispatchEvent(new Event('resize'));

    renderWithTheme(
      <Layout apiStatus={mockApiStatus}>
        {mockChildren}
      </Layout>
    );

    const menuButton = screen.getByLabelText('open drawer');
    fireEvent.click(menuButton);

    // Check if drawer content is visible
    expect(screen.getByText('Infra Automation')).toBeInTheDocument();
  });

  it('handles navigation', () => {
    renderWithTheme(
      <Layout apiStatus={mockApiStatus}>
        {mockChildren}
      </Layout>
    );

    // Click on a navigation item
    fireEvent.click(screen.getByText('Security'));
    
    // Check if the URL has changed
    expect(window.location.pathname).toBe('/security');
  });

  it('displays profile menu on click', () => {
    renderWithTheme(
      <Layout apiStatus={mockApiStatus}>
        {mockChildren}
      </Layout>
    );

    const profileButton = screen.getByLabelText('account of current user');
    fireEvent.click(profileButton);

    // Check if menu items are displayed
    expect(screen.getByText('Profile')).toBeInTheDocument();
    expect(screen.getByText('My account')).toBeInTheDocument();
    expect(screen.getByText('Logout')).toBeInTheDocument();
  });

  it('displays notifications on click', () => {
    renderWithTheme(
      <Layout apiStatus={mockApiStatus}>
        {mockChildren}
      </Layout>
    );

    const notificationButton = screen.getByLabelText('Notifications');
    fireEvent.click(notificationButton);

    // Check if notifications are displayed
    expect(screen.getByText('Infrastructure Generated')).toBeInTheDocument();
    expect(screen.getByText('Security Review Complete')).toBeInTheDocument();
    expect(screen.getByText('API Status Change')).toBeInTheDocument();
  });

  it('updates page title based on current route', () => {
    render(
      <MemoryRouter initialEntries={['/security']}>
        <ThemeProvider theme={theme}>
          <Layout apiStatus={mockApiStatus}>
            {mockChildren}
          </Layout>
        </ThemeProvider>
      </MemoryRouter>
    );

    expect(screen.getByText('Security')).toBeInTheDocument();
  });

  it('displays correct status colors', () => {
    renderWithTheme(
      <Layout apiStatus={mockApiStatus}>
        {mockChildren}
      </Layout>
    );

    const onlineStatus = screen.getByText('API: online').closest('.MuiChip-root');
    expect(onlineStatus).toHaveClass('MuiChip-colorSuccess');

    const runningStatus = screen.getByText('Infrastructure: running').closest('.MuiChip-root');
    expect(runningStatus).toHaveClass('MuiChip-colorSuccess');
  });

  it('handles theme toggle', () => {
    renderWithTheme(
      <Layout apiStatus={mockApiStatus}>
        {mockChildren}
      </Layout>
    );

    const themeButton = screen.getByLabelText('Toggle light/dark mode');
    fireEvent.click(themeButton);
    
    // Note: Actual theme change would need to be tested at a higher level
    // where the theme context is managed
  });
}); 