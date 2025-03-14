import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  AppBar,
  Box,
  CssBaseline,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  Badge,
  Avatar,
  Tooltip,
  Menu,
  MenuItem,
  useTheme,
  useMediaQuery,
  Chip,
  ListSubheader
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  Code as CodeIcon,
  Security as SecurityIcon,
  History as HistoryIcon,
  Visibility as VisibilityIcon,
  Settings as SettingsIcon,
  Notifications as NotificationsIcon,
  AccountCircle,
  Brightness4 as DarkModeIcon,
  Brightness7 as LightModeIcon,
  ChevronLeft as ChevronLeftIcon,
  Money as MoneyIcon,
  Assignment as JiraIcon,
  Description as ConfluenceIcon,
  GitHub as GitHubIcon,
  Cloud as NexusIcon,
  CloudQueue as KubernetesIcon,
  CloudSync as ArgoCDIcon,
  Storage as StorageIcon,
  Build as BuildIcon,
  Analytics as AnalyticsIcon,
  AccountTree as WorkflowIcon
} from '@mui/icons-material';

const drawerWidth = 240;

function Layout({ children, apiStatus }) {
  const theme = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  
  const [mobileOpen, setMobileOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState(null);
  const [notificationAnchorEl, setNotificationAnchorEl] = useState(null);
  
  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleProfileMenuOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleProfileMenuClose = () => {
    setAnchorEl(null);
  };

  const handleNotificationMenuOpen = (event) => {
    setNotificationAnchorEl(event.currentTarget);
  };

  const handleNotificationMenuClose = () => {
    setNotificationAnchorEl(null);
  };

  // Navigation items grouped by category
  const navigationItems = [
    {
      category: 'Overview',
      items: [
        { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
        { text: 'Infrastructure', icon: <CodeIcon />, path: '/infrastructure' },
        { text: 'Security', icon: <SecurityIcon />, path: '/security' },
        { text: 'Cost', icon: <MoneyIcon />, path: '/cost' },
        { text: 'Infrastructure Generator', icon: <CodeIcon />, path: '/generate' },
        { text: 'Security Review', icon: <SecurityIcon />, path: '/security' },
        { text: 'Task History', icon: <HistoryIcon />, path: '/tasks' },
        { text: 'Visualization', icon: <VisibilityIcon />, path: '/visualize' },
        { text: 'Workflow Editor', icon: <WorkflowIcon />, path: '/workflow' }
      ]
    },
    {
      category: 'Development',
      items: [
        { text: 'Jira', icon: <JiraIcon />, path: '/jira' },
        { text: 'Confluence', icon: <ConfluenceIcon />, path: '/confluence' },
        { text: 'GitHub', icon: <GitHubIcon />, path: '/github' }
      ]
    },
    {
      category: 'DevOps',
      items: [
        { text: 'Nexus', icon: <NexusIcon />, path: '/nexus' },
        { text: 'Kubernetes', icon: <KubernetesIcon />, path: '/kubernetes' },
        { text: 'ArgoCD', icon: <ArgoCDIcon />, path: '/argocd' }
      ]
    },
    {
      category: 'Monitoring',
      items: [
        { text: 'Observability', icon: <VisibilityIcon />, path: '/observability' },
        { text: 'Analytics', icon: <AnalyticsIcon />, path: '/analytics' }
      ]
    },
    {
      category: 'Settings',
      items: [
        { text: 'History', icon: <HistoryIcon />, path: '/history' },
        { text: 'Settings', icon: <SettingsIcon />, path: '/settings' }
      ]
    }
  ];

  const getStatusColor = (status) => {
    switch (status) {
      case 'online':
        return 'success';
      case 'offline':
        return 'error';
      case 'busy':
        return 'warning';
      default:
        return 'default';
    }
  };

  const drawer = (
    <div>
      <Toolbar>
        <Typography variant="h6" noWrap component="div">
          Infra Automation
        </Typography>
      </Toolbar>
      <Divider />
      {navigationItems.map(({ category, items }) => (
        <React.Fragment key={category}>
          <List
            subheader={
              <ListSubheader component="div" id={`${category}-subheader`}>
                {category}
              </ListSubheader>
            }
          >
            {items.map(({ text, icon, path }) => (
              <ListItem key={text} disablePadding>
                <ListItemButton
                  selected={location.pathname === path}
                  onClick={() => {
                    navigate(path);
                    if (isMobile) {
                      setMobileOpen(false);
                    }
                  }}
                >
                  <ListItemIcon>{icon}</ListItemIcon>
                  <ListItemText primary={text} />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
          <Divider />
        </React.Fragment>
      ))}
      <Divider />
      <Box sx={{ p: 2 }}>
        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
          System Status
        </Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          <Chip
            label={`API: ${apiStatus.status}`}
            color={getStatusColor(apiStatus.status)}
            size="small"
            sx={{ justifyContent: 'flex-start' }}
          />
          {apiStatus.agents && apiStatus.agents.map((agent) => (
            <Chip
              key={agent.name}
              label={`${agent.name}: ${agent.status}`}
              color={getStatusColor(agent.status)}
              size="small"
              sx={{ justifyContent: 'flex-start' }}
            />
          ))}
        </Box>
      </Box>
    </div>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      <AppBar
        position="fixed"
        sx={{
          width: { md: `calc(100% - ${drawerWidth}px)` },
          ml: { md: `${drawerWidth}px` },
          boxShadow: 2,
          backgroundColor: 'background.paper',
          color: 'text.primary',
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { md: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography
            variant="h6"
            noWrap
            component="div"
            sx={{ display: { xs: 'none', sm: 'block' }, flexGrow: 1 }}
          >
            {navigationItems.find((item) => item.items.find((i) => i.path === location.pathname))?.items.find((i) => i.path === location.pathname)?.text || 'Not Found'}
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Tooltip title="Toggle light/dark mode">
              <IconButton color="inherit" sx={{ mr: 1 }}>
                {theme.palette.mode === 'dark' ? <LightModeIcon /> : <DarkModeIcon />}
              </IconButton>
            </Tooltip>
            <Tooltip title="Notifications">
              <IconButton
                color="inherit"
                onClick={handleNotificationMenuOpen}
                sx={{ mr: 1 }}
              >
                <Badge badgeContent={3} color="error">
                  <NotificationsIcon />
                </Badge>
              </IconButton>
            </Tooltip>
            <Tooltip title="Account">
              <IconButton
                edge="end"
                aria-label="account of current user"
                aria-haspopup="true"
                onClick={handleProfileMenuOpen}
                color="inherit"
              >
                <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main' }}>
                  <AccountCircle />
                </Avatar>
              </IconButton>
            </Tooltip>
          </Box>
        </Toolbar>
      </AppBar>
      <Box
        component="nav"
        sx={{ width: { md: drawerWidth }, flexShrink: { md: 0 } }}
        aria-label="mailbox folders"
      >
        <Drawer
          variant={isMobile ? 'temporary' : 'permanent'}
          open={isMobile ? mobileOpen : true}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true, // Better open performance on mobile.
          }}
          sx={{
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
              borderRight: '1px solid rgba(0, 0, 0, 0.12)',
              boxShadow: 'none',
            },
          }}
        >
          {drawer}
        </Drawer>
      </Box>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 0,
          width: { md: `calc(100% - ${drawerWidth}px)` },
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <Toolbar />
        {children}
      </Box>
      
      {/* Profile Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleProfileMenuClose}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        <MenuItem onClick={handleProfileMenuClose}>Profile</MenuItem>
        <MenuItem onClick={handleProfileMenuClose}>My account</MenuItem>
        <MenuItem onClick={handleProfileMenuClose}>Logout</MenuItem>
      </Menu>
      
      {/* Notifications Menu */}
      <Menu
        anchorEl={notificationAnchorEl}
        open={Boolean(notificationAnchorEl)}
        onClose={handleNotificationMenuClose}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
        PaperProps={{
          sx: { width: 320, maxHeight: 400 }
        }}
      >
        <MenuItem onClick={handleNotificationMenuClose}>
          <Box sx={{ width: '100%' }}>
            <Typography variant="subtitle2">Infrastructure Generated</Typography>
            <Typography variant="body2" color="text.secondary">
              AWS infrastructure was successfully generated
            </Typography>
            <Typography variant="caption" color="text.secondary">
              2 minutes ago
            </Typography>
          </Box>
        </MenuItem>
        <Divider />
        <MenuItem onClick={handleNotificationMenuClose}>
          <Box sx={{ width: '100%' }}>
            <Typography variant="subtitle2">Security Review Complete</Typography>
            <Typography variant="body2" color="text.secondary">
              3 issues found in your infrastructure
            </Typography>
            <Typography variant="caption" color="text.secondary">
              10 minutes ago
            </Typography>
          </Box>
        </MenuItem>
        <Divider />
        <MenuItem onClick={handleNotificationMenuClose}>
          <Box sx={{ width: '100%' }}>
            <Typography variant="subtitle2">API Status Change</Typography>
            <Typography variant="body2" color="text.secondary">
              API is now online
            </Typography>
            <Typography variant="caption" color="text.secondary">
              1 hour ago
            </Typography>
          </Box>
        </MenuItem>
      </Menu>
    </Box>
  );
}

export default Layout; 