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
  Storage as StorageIcon
} from '@mui/icons-material';

const AgentStatus = ({ agents }) => {
  // Helper function to get agent icon
  const getAgentIcon = (agentType) => {
    const type = agentType.toLowerCase();
    if (type.includes('infrastructure')) return <CodeIcon />;
    if (type.includes('architect')) return <ArchitectureIcon />;
    if (type.includes('security')) return <SecurityIcon />;
    if (type.includes('cost')) return <MoneyIcon />;
    if (type.includes('terraform')) return <StorageIcon />;
    return <CodeIcon />;
  };

  // Helper function to get status color
  const getStatusColor = (status) => {
    if (!status) return 'default';
    
    status = status.toLowerCase();
    if (status === 'idle' || status === 'online' || status === 'running') return 'success';
    if (status === 'processing' || status === 'busy') return 'warning';
    if (status === 'error' || status === 'offline') return 'error';
    return 'default';
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
    switch (agentType.toLowerCase()) {
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
                      color={getStatusColor(agent.status)}
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