import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  TextField,
  Button,
  Grid,
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  Snackbar
} from '@mui/material';
import {
  AttachMoney as MoneyIcon,
  TrendingDown as SavingsIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  CheckCircle as CheckCircleIcon,
  History as HistoryIcon
} from '@mui/icons-material';
import { optimizeCosts } from '../services/api';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';
import LoadingIndicator from '../components/LoadingIndicator';

function CostOptimization() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [formData, setFormData] = useState({
    infrastructure_code: '',
    iac_type: 'terraform',
    cloud_provider: 'aws'
  });
  const [result, setResult] = useState(null);
  const [showBackgroundProcessingAlert, setShowBackgroundProcessingAlert] = useState(false);
  const [taskId, setTaskId] = useState(null);

  const cloudProviders = [
    { value: 'aws', label: 'Amazon Web Services (AWS)' },
    { value: 'azure', label: 'Microsoft Azure' },
    { value: 'gcp', label: 'Google Cloud Platform (GCP)' }
  ];

  const iacTypes = [
    { value: 'terraform', label: 'Terraform' },
    { value: 'ansible', label: 'Ansible' },
    { value: 'jenkins', label: 'Jenkins' }
  ];

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setShowBackgroundProcessingAlert(false);

    try {
      const response = await optimizeCosts(formData);
      setResult(response);
      if (response.task_id) {
        setTaskId(response.task_id);
      }
    } catch (err) {
      console.error('Failed to optimize costs:', err);
      let errorMessage = 'Failed to optimize costs. Please try again later.';
      
      if (err.code === 'ECONNABORTED') {
        errorMessage = 'The request timed out. Cost optimization is taking longer than expected. The system will continue processing your request in the background.';
        setShowBackgroundProcessingAlert(true);
        if (err.config && err.config.url && err.config.url.includes('task_id=')) {
          const urlParams = new URLSearchParams(err.config.url.split('?')[1]);
          setTaskId(urlParams.get('task_id'));
        }
      } else if (err.response) {
        if (err.response.data && err.response.data.detail) {
          errorMessage = `Error: ${err.response.data.detail}`;
        } else if (err.response.status === 500) {
          errorMessage = 'The server encountered an error while processing your request. Please try again later.';
        } else if (err.response.status === 400) {
          errorMessage = 'Invalid request. Please check your inputs and try again.';
        }
      } else if (!navigator.onLine) {
        errorMessage = 'You appear to be offline. Please check your internet connection and try again.';
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleViewTaskHistory = () => {
    navigate('/tasks');
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  return (
    <Box className="slide-in-up">
      <Typography variant="h4" component="h1" gutterBottom>
        Cost Optimization
      </Typography>
      <Typography variant="body1" paragraph>
        Analyze and optimize your infrastructure costs while maintaining performance and reliability.
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Submit Infrastructure Code
            </Typography>
            <Box component="form" onSubmit={handleSubmit}>
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <TextField
                    required
                    fullWidth
                    label="Infrastructure Code"
                    name="infrastructure_code"
                    value={formData.infrastructure_code}
                    onChange={handleInputChange}
                    placeholder="Paste your infrastructure code here"
                    multiline
                    rows={10}
                  />
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel id="iac-type-label">IaC Type</InputLabel>
                    <Select
                      labelId="iac-type-label"
                      name="iac_type"
                      value={formData.iac_type}
                      label="IaC Type"
                      onChange={handleInputChange}
                    >
                      {iacTypes.map((type) => (
                        <MenuItem key={type.value} value={type.value}>
                          {type.label}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel id="cloud-provider-label">Cloud Provider</InputLabel>
                    <Select
                      labelId="cloud-provider-label"
                      name="cloud_provider"
                      value={formData.cloud_provider}
                      label="Cloud Provider"
                      onChange={handleInputChange}
                    >
                      {cloudProviders.map((provider) => (
                        <MenuItem key={provider.value} value={provider.value}>
                          {provider.label}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={12}>
                  <Button
                    type="submit"
                    variant="contained"
                    color="primary"
                    fullWidth
                    disabled={loading || !formData.infrastructure_code}
                    startIcon={<MoneyIcon />}
                  >
                    Optimize Costs
                  </Button>
                </Grid>

                <Grid item xs={12}>
                  <Button
                    variant="outlined"
                    color="primary"
                    fullWidth
                    onClick={handleViewTaskHistory}
                    startIcon={<HistoryIcon />}
                  >
                    View Task History
                  </Button>
                </Grid>
              </Grid>
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          {loading && <LoadingIndicator message="Analyzing infrastructure costs..." />}
          
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          {showBackgroundProcessingAlert && (
            <Alert severity="info" sx={{ mb: 2 }}>
              Your request is being processed in the background. You can check the results in the task history.
              {taskId && (
                <Typography variant="body2" sx={{ mt: 1 }}>
                  Task ID: {taskId}
                </Typography>
              )}
            </Alert>
          )}

          {result && (
            <Box>
              <Card sx={{ mb: 2 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Cost Analysis Summary
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                      <Typography variant="subtitle2" color="textSecondary">
                        Current Estimated Cost
                      </Typography>
                      <Typography variant="h5">
                        {formatCurrency(result.cost_analysis?.current_estimated_cost || 0)}
                      </Typography>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Typography variant="subtitle2" color="textSecondary">
                        Potential Savings
                      </Typography>
                      <Typography variant="h5" color="success.main">
                        {formatCurrency(result.cost_analysis?.potential_savings || 0)}
                      </Typography>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>

              <Card sx={{ mb: 2 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Optimization Opportunities
                  </Typography>
                  <List>
                    {result.cost_analysis && result.cost_analysis.optimization_opportunities && 
                      result.cost_analysis.optimization_opportunities.map((opportunity, index) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          <SavingsIcon color="primary" />
                        </ListItemIcon>
                        <ListItemText
                          primary={opportunity.category}
                          secondary={opportunity.description}
                        />
                        <Chip
                          label={formatCurrency(opportunity.potential_savings)}
                          color="success"
                          size="small"
                        />
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>

              {result.optimized_code && (
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Optimized Infrastructure Code
                    </Typography>
                    <SyntaxHighlighter
                      language="hcl"
                      style={tomorrow}
                      customStyle={{
                        margin: 0,
                        borderRadius: 4,
                        maxHeight: 400,
                        overflow: 'auto'
                      }}
                    >
                      {result.optimized_code}
                    </SyntaxHighlighter>
                  </CardContent>
                </Card>
              )}
            </Box>
          )}
        </Grid>
      </Grid>
    </Box>
  );
}

export default CostOptimization; 