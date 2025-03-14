import React from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Chip,
  Tooltip,
  Card,
  CardContent
} from '@mui/material';
import {
  Code as CodeIcon,
  Architecture as ArchitectureIcon,
  Security as SecurityIcon,
  AttachMoney as MoneyIcon,
  Storage as StorageIcon,
  Assignment as JiraIcon,
  Description as ConfluenceIcon,
  GitHub as GitHubIcon,
  Cloud as NexusIcon,
  CloudQueue as KubernetesIcon,
  CloudSync as ArgoCDIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  CheckCircle as CheckCircleIcon,
  HourglassEmpty as HourglassIcon
} from '@mui/icons-material';

const AgentStatus = ({ agents = [] }) => {
  // Helper function to get agent icon
  const getAgentIcon = (agentName, capabilities) => {
    if (!agentName) return <CodeIcon />;
    const name = String(agentName || '').toLowerCase();
    
    // Check capabilities first for more accurate icon selection
    if (capabilities?.includes('terraform_generation')) return <StorageIcon />;
    if (capabilities?.includes('cost_estimation')) return <MoneyIcon />;
    
    // Fall back to name-based icon selection
    if (name.includes('infrastructure')) return <CodeIcon />;
    if (name.includes('architect')) return <ArchitectureIcon />;
    if (name.includes('security')) return <SecurityIcon />;
    if (name.includes('jira')) return <JiraIcon />;
    if (name.includes('confluence')) return <ConfluenceIcon />;
    if (name.includes('github')) return <GitHubIcon />;
    if (name.includes('nexus')) return <NexusIcon />;
    if (name.includes('kubernetes')) return <KubernetesIcon />;
    if (name.includes('argocd')) return <ArgoCDIcon />;
    return <CodeIcon />;
  };

  // Helper function to get status info
  const getStatusInfo = (state) => {
    if (!state) return { icon: <WarningIcon />, color: 'default', label: 'Unknown' };
    
    const stateStr = String(state || '').toLowerCase();
    switch (stateStr) {
      case 'healthy':
      case 'running':
      case 'idle':
        return { icon: <CheckCircleIcon />, color: 'success', label: 'Running' };
      case 'error':
      case 'unhealthy':
        return { icon: <ErrorIcon />, color: 'error', label: 'Error' };
      case 'degraded':
      case 'missing_dependencies':
        return { icon: <WarningIcon />, color: 'warning', label: 'Degraded' };
      case 'not_initialized':
      case 'starting':
        return { icon: <HourglassIcon />, color: 'info', label: 'Starting' };
      default:
        return { icon: <WarningIcon />, color: 'default', label: stateStr };
    }
  };

  // Check if agents is an array or an object
  const agentsArray = Array.isArray(agents) 
    ? agents 
    : Object.entries(agents).map(([type, data]) => ({
        name: type.charAt(0).toUpperCase() + type.slice(1),
        description: getAgentDescription(type),
        status: data.status,
        last_active_time: data.last_active,
        id: type
      }));

  // Helper function to get agent description (used for object format)
  const getAgentDescription = (agentType) => {
    if (!agentType) return 'AI agent for infrastructure automation';
    
    switch (String(agentType).toLowerCase()) {
      case 'infrastructure':
        return 'Generates infrastructure as code based on requirements';
      case 'architecture':
        return 'Designs and optimizes system architecture';
      case 'security':
        return 'Analyzes infrastructure for security vulnerabilities';
      case 'cost':
        return 'Optimizes infrastructure for cost efficiency';
      case 'terraform_module':
        return 'Creates enterprise-grade Terraform modules following best practices';
      default:
        return 'AI agent for infrastructure automation';
    }
  };

  return (
    <Card sx={{ mb: 4 }}>
      <CardContent>
        <Typography variant="h5" gutterBottom>
          Agent Status
        </Typography>
        <Grid container spacing={3}>
          {agentsArray.map((agent, index) => (
            <Grid item xs={12} sm={6} md={4} lg={3} key={agent.id || index}>
              <Tooltip title={agent.description || "AI agent for infrastructure automation"}>
                <Paper
                  elevation={0}
                  sx={{
                    p: 2,
                    borderRadius: 2,
                    boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
                    height: '100%',
                    border: '1px solid rgba(0,0,0,0.08)',
                    transition: 'transform 0.3s ease-in-out, box-shadow 0.3s ease-in-out',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: '0 8px 16px rgba(0,0,0,0.1)',
                    },
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <Box
                      sx={{
                        backgroundColor: 'primary.light',
                        borderRadius: '50%',
                        p: 1,
                        mr: 2,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      {getAgentIcon(agent.name)}
                    </Box>
                    <Typography variant="h6">
                      {agent.name}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Typography variant="body2" color="text.secondary">
                      Status
                    </Typography>
                    <Chip
                      label={agent.status || 'unknown'}
                      color={getStatusInfo(agent.status).color}
                      size="small"
                    />
                  </Box>
                  {agent.last_active_time && (
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mt: 1 }}>
                      <Typography variant="body2" color="text.secondary">
                        Last Active
                      </Typography>
                      <Typography variant="body2">
                        {new Date(agent.last_active_time * 1000).toLocaleTimeString()}
                      </Typography>
                    </Box>
                  )}
                </Paper>
              </Tooltip>
            </Grid>
          ))}
        </Grid>
      </CardContent>
    </Card>
  );
};

export default AgentStatus; 