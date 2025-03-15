import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  IconButton,
  Tooltip,
  Divider,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Link
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Visibility as VisibilityIcon,
  VpnKey as KeyIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Pending as PendingIcon
} from '@mui/icons-material';
import { fetchEnvironments, createEnvironment, deleteEnvironment, fetchEnvironmentCredentials } from '../services/api';
import { formatDistanceToNow } from 'date-fns';

function Environments() {
  const [environments, setEnvironments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [openCreateDialog, setOpenCreateDialog] = useState(false);
  const [openCredentialsDialog, setOpenCredentialsDialog] = useState(false);
  const [selectedEnvironment, setSelectedEnvironment] = useState(null);
  const [credentials, setCredentials] = useState(null);
  const [credentialsLoading, setCredentialsLoading] = useState(false);
  const [formData, setFormData] = useState({
    environment_name: '',
    environment_type: 'development',
    user_id: 'user123',
    tools: ['jira', 'gitlab', 'jenkins'],
    custom_domain: '',
    resource_limits: {
      cpu: 2,
      memory: '4Gi'
    },
    description: ''
  });

  useEffect(() => {
    loadEnvironments();
    // Poll for updates every 10 seconds
    const interval = setInterval(loadEnvironments, 10000);
    return () => clearInterval(interval);
  }, []);

  const loadEnvironments = async () => {
    try {
      setLoading(true);
      const data = await fetchEnvironments();
      setEnvironments(data.environments || []);
    } catch (error) {
      console.error('Error loading environments:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateEnvironment = async () => {
    try {
      setLoading(true);
      await createEnvironment(formData);
      setOpenCreateDialog(false);
      // Reset form
      setFormData({
        environment_name: '',
        environment_type: 'development',
        user_id: 'user123',
        tools: ['jira', 'gitlab', 'jenkins'],
        custom_domain: '',
        resource_limits: {
          cpu: 2,
          memory: '4Gi'
        },
        description: ''
      });
      // Reload environments
      await loadEnvironments();
    } catch (error) {
      console.error('Error creating environment:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteEnvironment = async (environmentId) => {
    if (window.confirm('Are you sure you want to delete this environment?')) {
      try {
        setLoading(true);
        await deleteEnvironment(environmentId);
        await loadEnvironments();
      } catch (error) {
        console.error('Error deleting environment:', error);
      } finally {
        setLoading(false);
      }
    }
  };

  const handleViewCredentials = async (environment) => {
    setSelectedEnvironment(environment);
    setCredentialsLoading(true);
    setOpenCredentialsDialog(true);
    
    try {
      const data = await fetchEnvironmentCredentials(environment.environment_id);
      setCredentials(data.credentials || {});
    } catch (error) {
      console.error('Error fetching credentials:', error);
      setCredentials({});
    } finally {
      setCredentialsLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };

  const handleToolsChange = (e) => {
    setFormData({
      ...formData,
      tools: e.target.value
    });
  };

  const getStatusChip = (status) => {
    switch (status) {
      case 'running':
        return <Chip icon={<CheckCircleIcon />} label="Running" color="success" size="small" />;
      case 'creating':
      case 'starting':
        return <Chip icon={<PendingIcon />} label={status} color="warning" size="small" />;
      case 'failed':
        return <Chip icon={<ErrorIcon />} label="Failed" color="error" size="small" />;
      default:
        return <Chip label={status} size="small" />;
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Development Environments
        </Typography>
        <Box>
          <Tooltip title="Refresh">
            <IconButton onClick={loadEnvironments} disabled={loading}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setOpenCreateDialog(true)}
            sx={{ ml: 1 }}
          >
            Create Environment
          </Button>
        </Box>
      </Box>

      {loading && environments.length === 0 ? (
        <Box display="flex" justifyContent="center" p={3}>
          <CircularProgress />
        </Box>
      ) : environments.length === 0 ? (
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <Typography variant="body1" color="textSecondary">
            No environments found. Create your first environment to get started.
          </Typography>
        </Paper>
      ) : (
        <Grid container spacing={3}>
          {environments.map((env) => (
            <Grid item xs={12} md={6} lg={4} key={env.environment_id}>
              <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardContent sx={{ flexGrow: 1 }}>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                    <Typography variant="h6" component="div">
                      {env.environment_name}
                    </Typography>
                    {getStatusChip(env.status)}
                  </Box>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Type: {env.environment_type}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Created: {formatDistanceToNow(new Date(env.created_at), { addSuffix: true })}
                  </Typography>
                  
                  {env.ready && env.access_url && (
                    <Box mt={2}>
                      <Typography variant="subtitle2">Access URL:</Typography>
                      <Link href={env.access_url} target="_blank" rel="noopener noreferrer">
                        {env.access_url}
                      </Link>
                    </Box>
                  )}
                  
                  {env.ready && env.tool_endpoints && Object.keys(env.tool_endpoints).length > 0 && (
                    <Box mt={2}>
                      <Typography variant="subtitle2" gutterBottom>Available Tools:</Typography>
                      <Box display="flex" flexWrap="wrap" gap={1}>
                        {Object.keys(env.tool_endpoints)
                          .filter(tool => tool !== 'dashboard')
                          .map(tool => (
                            <Chip 
                              key={tool}
                              label={tool}
                              size="small"
                              component="a"
                              href={env.tool_endpoints[tool]}
                              target="_blank"
                              rel="noopener noreferrer"
                              clickable
                            />
                          ))}
                      </Box>
                    </Box>
                  )}
                </CardContent>
                <Divider />
                <CardActions>
                  {env.ready && (
                    <Button 
                      size="small" 
                      startIcon={<KeyIcon />}
                      onClick={() => handleViewCredentials(env)}
                    >
                      Credentials
                    </Button>
                  )}
                  <Button 
                    size="small" 
                    color="error" 
                    startIcon={<DeleteIcon />}
                    onClick={() => handleDeleteEnvironment(env.environment_id)}
                  >
                    Delete
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Create Environment Dialog */}
      <Dialog open={openCreateDialog} onClose={() => setOpenCreateDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Environment</DialogTitle>
        <DialogContent>
          <Box component="form" sx={{ mt: 2 }}>
            <TextField
              fullWidth
              margin="normal"
              label="Environment Name"
              name="environment_name"
              value={formData.environment_name}
              onChange={handleInputChange}
              required
            />
            
            <FormControl fullWidth margin="normal">
              <InputLabel>Environment Type</InputLabel>
              <Select
                name="environment_type"
                value={formData.environment_type}
                onChange={handleInputChange}
                label="Environment Type"
              >
                <MenuItem value="development">Development</MenuItem>
                <MenuItem value="testing">Testing</MenuItem>
                <MenuItem value="staging">Staging</MenuItem>
                <MenuItem value="production">Production</MenuItem>
                <MenuItem value="demo">Demo</MenuItem>
              </Select>
            </FormControl>
            
            <FormControl fullWidth margin="normal">
              <InputLabel>Tools</InputLabel>
              <Select
                multiple
                name="tools"
                value={formData.tools}
                onChange={handleToolsChange}
                label="Tools"
                renderValue={(selected) => (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {selected.map((value) => (
                      <Chip key={value} label={value} />
                    ))}
                  </Box>
                )}
              >
                <MenuItem value="jira">Jira</MenuItem>
                <MenuItem value="confluence">Confluence</MenuItem>
                <MenuItem value="gitlab">GitLab</MenuItem>
                <MenuItem value="jenkins">Jenkins</MenuItem>
                <MenuItem value="nexus">Nexus</MenuItem>
                <MenuItem value="vault">Vault</MenuItem>
                <MenuItem value="kubernetes">Kubernetes</MenuItem>
                <MenuItem value="prometheus">Prometheus</MenuItem>
                <MenuItem value="grafana">Grafana</MenuItem>
                <MenuItem value="all">All Tools</MenuItem>
              </Select>
            </FormControl>
            
            <TextField
              fullWidth
              margin="normal"
              label="Custom Domain (Optional)"
              name="custom_domain"
              value={formData.custom_domain}
              onChange={handleInputChange}
            />
            
            <TextField
              fullWidth
              margin="normal"
              label="Description"
              name="description"
              value={formData.description}
              onChange={handleInputChange}
              multiline
              rows={3}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenCreateDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleCreateEnvironment} 
            variant="contained" 
            disabled={!formData.environment_name || loading}
          >
            {loading ? <CircularProgress size={24} /> : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Credentials Dialog */}
      <Dialog 
        open={openCredentialsDialog} 
        onClose={() => setOpenCredentialsDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Environment Credentials
          {selectedEnvironment && (
            <Typography variant="subtitle1" color="text.secondary">
              {selectedEnvironment.environment_name}
            </Typography>
          )}
        </DialogTitle>
        <DialogContent>
          {credentialsLoading ? (
            <Box display="flex" justifyContent="center" p={3}>
              <CircularProgress />
            </Box>
          ) : credentials ? (
            <TableContainer component={Paper} sx={{ mt: 2 }}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Tool</TableCell>
                    <TableCell>Username</TableCell>
                    <TableCell>Password/Token</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {Object.entries(credentials).map(([tool, creds]) => (
                    <TableRow key={tool}>
                      <TableCell>{tool}</TableCell>
                      <TableCell>{creds.username || 'N/A'}</TableCell>
                      <TableCell>{creds.password || creds.token || 'N/A'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          ) : (
            <Typography>No credentials available</Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenCredentialsDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default Environments; 