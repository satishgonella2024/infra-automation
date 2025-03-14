import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  Alert,
  Paper,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Tabs,
  Tab
} from '@mui/material';
import {
  CloudQueue as KubernetesIcon,
  Storage as DeploymentIcon,
  Security as SecurityIcon,
  Speed as PerformanceIcon,
  NetworkCheck as NetworkIcon,
  Memory as ResourceIcon
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';

const TabPanel = (props) => {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`kubernetes-tabpanel-${index}`}
      aria-labelledby={`kubernetes-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
};

const Kubernetes = () => {
  const theme = useTheme();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [tabValue, setTabValue] = useState(0);
  const [action, setAction] = useState('generate_manifests');
  const [formData, setFormData] = useState({
    name: '',
    namespace: 'default',
    replicas: 1,
    image: '',
    containerPort: 80,
    resourceLimits: {
      cpu: '500m',
      memory: '512Mi'
    }
  });

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch('/api/kubernetes', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          action,
          parameters: formData
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to process Kubernetes request');
      }

      setSuccess('Operation completed successfully');
      if (action === 'generate_manifests') {
        setFormData({
          ...formData,
          name: '',
          image: ''
        });
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    if (name.includes('.')) {
      const [parent, child] = name.split('.');
      setFormData(prev => ({
        ...prev,
        [parent]: {
          ...prev[parent],
          [child]: value
        }
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: value
      }));
    }
  };

  const renderDeploymentForm = () => (
    <form onSubmit={handleSubmit}>
      <Grid container spacing={2}>
        <Grid item xs={12}>
          <TextField
            fullWidth
            label="Application Name"
            name="name"
            value={formData.name}
            onChange={handleChange}
            required
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="Namespace"
            name="namespace"
            value={formData.namespace}
            onChange={handleChange}
            required
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="Replicas"
            name="replicas"
            type="number"
            value={formData.replicas}
            onChange={handleChange}
            required
            inputProps={{ min: 1 }}
          />
        </Grid>
        <Grid item xs={12}>
          <TextField
            fullWidth
            label="Container Image"
            name="image"
            value={formData.image}
            onChange={handleChange}
            required
            helperText="e.g., nginx:latest"
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="Container Port"
            name="containerPort"
            type="number"
            value={formData.containerPort}
            onChange={handleChange}
            required
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="CPU Limit"
            name="resourceLimits.cpu"
            value={formData.resourceLimits.cpu}
            onChange={handleChange}
            helperText="e.g., 500m, 1"
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="Memory Limit"
            name="resourceLimits.memory"
            value={formData.resourceLimits.memory}
            onChange={handleChange}
            helperText="e.g., 512Mi, 1Gi"
          />
        </Grid>
        <Grid item xs={12}>
          <Button
            type="submit"
            variant="contained"
            fullWidth
            disabled={loading}
            sx={{ mt: 2 }}
          >
            {loading ? <CircularProgress size={24} /> : 'Generate Manifests'}
          </Button>
        </Grid>
      </Grid>
    </form>
  );

  const renderAnalysisForm = () => (
    <form onSubmit={handleSubmit}>
      <Grid container spacing={2}>
        <Grid item xs={12}>
          <TextField
            fullWidth
            label="Namespace"
            name="namespace"
            value={formData.namespace}
            onChange={handleChange}
            required
          />
        </Grid>
        <Grid item xs={12}>
          <FormControl fullWidth>
            <InputLabel>Analysis Type</InputLabel>
            <Select
              value={formData.analysisType || 'security'}
              label="Analysis Type"
              name="analysisType"
              onChange={handleChange}
            >
              <MenuItem value="security">Security Analysis</MenuItem>
              <MenuItem value="performance">Performance Analysis</MenuItem>
              <MenuItem value="cost">Cost Analysis</MenuItem>
              <MenuItem value="best_practices">Best Practices</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={12}>
          <Button
            type="submit"
            variant="contained"
            fullWidth
            disabled={loading}
            sx={{ mt: 2 }}
          >
            {loading ? <CircularProgress size={24} /> : 'Run Analysis'}
          </Button>
        </Grid>
      </Grid>
    </form>
  );

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <KubernetesIcon fontSize="large" />
        Kubernetes Management
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Tabs
                value={tabValue}
                onChange={handleTabChange}
                indicatorColor="primary"
                textColor="primary"
                variant="fullWidth"
              >
                <Tab label="Deployment" icon={<DeploymentIcon />} />
                <Tab label="Analysis" icon={<SecurityIcon />} />
              </Tabs>

              <TabPanel value={tabValue} index={0}>
                {renderDeploymentForm()}
              </TabPanel>

              <TabPanel value={tabValue} index={1}>
                {renderAnalysisForm()}
              </TabPanel>

              {error && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  {error}
                </Alert>
              )}

              {success && (
                <Alert severity="success" sx={{ mt: 2 }}>
                  {success}
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Cluster Overview
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <List>
              <ListItem>
                <ListItemIcon>
                  <DeploymentIcon />
                </ListItemIcon>
                <ListItemText 
                  primary="Active Deployments"
                  secondary="12 running"
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <ResourceIcon />
                </ListItemIcon>
                <ListItemText 
                  primary="Resource Usage"
                  secondary="CPU: 65%, Memory: 78%"
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <NetworkIcon />
                </ListItemIcon>
                <ListItemText 
                  primary="Network Status"
                  secondary="All services healthy"
                />
              </ListItem>
            </List>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Kubernetes; 