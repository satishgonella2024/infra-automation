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
  CircularProgress,
  Alert,
  Card,
  CardContent,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  Snackbar
} from '@mui/material';
import {
  Security as SecurityIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  CheckCircle as CheckCircleIcon,
  Send as SendIcon,
  History as HistoryIcon
} from '@mui/icons-material';
import { reviewSecurity } from '../services/api';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';
import LoadingIndicator from '../components/LoadingIndicator';

const copyToClipboard = (text) => {
  // Check if the Clipboard API is available
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text)
      .then(() => {
        console.log('Text copied to clipboard');
      })
      .catch(err => {
        console.error('Failed to copy text: ', err);
        fallbackCopyToClipboard(text);
      });
  } else {
    // Fallback for browsers that don't support the Clipboard API
    fallbackCopyToClipboard(text);
  }
};

const fallbackCopyToClipboard = (text) => {
  try {
    // Create a temporary textarea element
    const textArea = document.createElement('textarea');
    textArea.value = text;
    
    // Make the textarea out of viewport
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    
    // Select and copy the text
    textArea.focus();
    textArea.select();
    const successful = document.execCommand('copy');
    
    // Clean up
    document.body.removeChild(textArea);
    
    if (successful) {
      console.log('Text copied to clipboard using fallback');
    } else {
      console.error('Fallback clipboard copy failed');
    }
  } catch (err) {
    console.error('Fallback clipboard copy failed: ', err);
  }
};

function SecurityReview() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [formData, setFormData] = useState({
    infrastructure_code: '',
    iac_type: 'terraform',
    cloud_provider: 'aws',
    compliance_framework: ''
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

  const complianceFrameworks = [
    { value: '', label: 'None (General Security Best Practices)' },
    { value: 'cis', label: 'CIS Benchmarks' },
    { value: 'hipaa', label: 'HIPAA' },
    { value: 'pci-dss', label: 'PCI DSS' },
    { value: 'nist', label: 'NIST Cybersecurity Framework' },
    { value: 'gdpr', label: 'GDPR' }
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
      const response = await reviewSecurity(formData);
      setResult(response);
      if (response.task_id) {
        setTaskId(response.task_id);
      }
    } catch (err) {
      console.error('Failed to review security:', err);
      let errorMessage = 'Failed to review security. Please try again later.';
      
      // Provide more specific error messages based on the error
      if (err.code === 'ECONNABORTED') {
        errorMessage = 'The request timed out. Security review is taking longer than expected. The system will continue processing your request in the background.';
        setShowBackgroundProcessingAlert(true);
        // Extract task ID from the URL if available
        if (err.config && err.config.url && err.config.url.includes('task_id=')) {
          const urlParams = new URLSearchParams(err.config.url.split('?')[1]);
          setTaskId(urlParams.get('task_id'));
        }
      } else if (err.response) {
        // If we have a response with an error message, use it
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

  const getSeverityIcon = (severity) => {
    switch (severity.toLowerCase()) {
      case 'critical':
      case 'high':
        return <ErrorIcon color="error" />;
      case 'medium':
        return <WarningIcon color="warning" />;
      case 'low':
        return <InfoIcon color="info" />;
      case 'info':
        return <InfoIcon color="disabled" />;
      default:
        return <InfoIcon />;
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity.toLowerCase()) {
      case 'critical':
      case 'high':
        return 'error';
      case 'medium':
        return 'warning';
      case 'low':
        return 'info';
      case 'info':
        return 'default';
      default:
        return 'default';
    }
  };

  return (
    <Box className="slide-in-up">
      <Typography variant="h4" component="h1" gutterBottom>
        Security Review
      </Typography>
      <Typography variant="body1" paragraph>
        Analyze your infrastructure code for security vulnerabilities and compliance issues.
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
                  <FormControl fullWidth>
                    <InputLabel id="compliance-framework-label">Compliance Framework (Optional)</InputLabel>
                    <Select
                      labelId="compliance-framework-label"
                      name="compliance_framework"
                      value={formData.compliance_framework}
                      label="Compliance Framework (Optional)"
                      onChange={handleInputChange}
                    >
                      {complianceFrameworks.map((framework) => (
                        <MenuItem key={framework.value} value={framework.value}>
                          {framework.label}
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
                    startIcon={<SecurityIcon />}
                  >
                    Analyze Security
                  </Button>
                </Grid>
              </Grid>
            </Box>
            
            {error && (
              <Alert 
                severity="error" 
                sx={{ mt: 2 }}
                action={
                  <Box sx={{ display: 'flex' }}>
                    {showBackgroundProcessingAlert && (
                      <Button 
                        color="inherit" 
                        size="small" 
                        onClick={handleViewTaskHistory}
                        startIcon={<HistoryIcon />}
                        sx={{ mr: 1 }}
                      >
                        View Tasks
                      </Button>
                    )}
                    <Button 
                      color="inherit" 
                      size="small" 
                      onClick={handleSubmit}
                      disabled={loading}
                    >
                      Retry
                    </Button>
                  </Box>
                }
              >
                {error}
              </Alert>
            )}
            
            {showBackgroundProcessingAlert && (
              <Alert 
                severity="info" 
                sx={{ mt: 2 }}
                action={
                  <Button 
                    color="inherit" 
                    size="small" 
                    onClick={handleViewTaskHistory}
                    startIcon={<HistoryIcon />}
                  >
                    View Tasks
                  </Button>
                }
              >
                Your security review request is being processed in the background. You can check the task history to see the results when it's complete.
              </Alert>
            )}
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: '100%', display: 'flex', flexDirection: 'column' }}>
            <Typography variant="h6" gutterBottom>
              Security Analysis Results
            </Typography>
            
            {loading ? (
              <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', flexGrow: 1 }}>
                <LoadingIndicator 
                  message="Analyzing security issues..." 
                  showProgress={true}
                  timeout={120} // 2 minutes timeout
                />
                <Typography variant="body2" color="text.secondary" sx={{ mt: 2, textAlign: 'center' }}>
                  We're using AI to analyze your infrastructure code for security vulnerabilities.
                </Typography>
              </Box>
            ) : !result ? (
              <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', flexGrow: 1 }}>
                <SecurityIcon sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
                <Typography variant="body1" color="text.secondary">
                  Submit your infrastructure code to see security analysis results.
                </Typography>
              </Box>
            ) : (
              <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
                {result.findings && result.findings.length > 0 ? (
                  <>
                    <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="subtitle1">
                        Found {result.findings.length} security issues
                      </Typography>
                      <Box>
                        {result.summary && result.summary.critical > 0 && (
                          <Chip 
                            label={`${result.summary.critical} Critical`} 
                            color="error" 
                            size="small" 
                            sx={{ mr: 1 }} 
                          />
                        )}
                        {result.summary && result.summary.high > 0 && (
                          <Chip 
                            label={`${result.summary.high} High`} 
                            color="error" 
                            size="small" 
                            sx={{ mr: 1 }} 
                          />
                        )}
                        {result.summary && result.summary.medium > 0 && (
                          <Chip 
                            label={`${result.summary.medium} Medium`} 
                            color="warning" 
                            size="small" 
                            sx={{ mr: 1 }} 
                          />
                        )}
                        {result.summary && result.summary.low > 0 && (
                          <Chip 
                            label={`${result.summary.low} Low`} 
                            color="info" 
                            size="small" 
                          />
                        )}
                      </Box>
                    </Box>
                    
                    <List sx={{ width: '100%' }}>
                      {result.findings.map((finding, index) => (
                        <React.Fragment key={index}>
                          <ListItem alignItems="flex-start">
                            <ListItemIcon>
                              {getSeverityIcon(finding.severity)}
                            </ListItemIcon>
                            <ListItemText
                              primary={
                                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                  <Typography variant="subtitle1" component="span">
                                    {finding.title || `Issue #${index + 1}`}
                                  </Typography>
                                  <Chip 
                                    label={finding.severity} 
                                    color={getSeverityColor(finding.severity)} 
                                    size="small" 
                                    sx={{ ml: 1 }} 
                                  />
                                </Box>
                              }
                              secondary={
                                <>
                                  <Typography variant="body2" component="span" color="text.primary">
                                    {finding.description}
                                  </Typography>
                                  {finding.location && (
                                    <Typography variant="body2" component="div" sx={{ mt: 1 }}>
                                      Location: {finding.location}
                                    </Typography>
                                  )}
                                  {finding.recommendation && (
                                    <Typography variant="body2" component="div" sx={{ mt: 1 }}>
                                      Recommendation: {finding.recommendation}
                                    </Typography>
                                  )}
                                </>
                              }
                            />
                          </ListItem>
                          {index < result.findings.length - 1 && <Divider variant="inset" component="li" />}
                        </React.Fragment>
                      ))}
                    </List>
                  </>
                ) : (
                  <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', flexGrow: 1 }}>
                    <CheckCircleIcon sx={{ fontSize: 60, color: 'success.main', mb: 2 }} />
                    <Typography variant="h6" color="success.main" gutterBottom>
                      No security issues found!
                    </Typography>
                    <Typography variant="body1" color="text.secondary" align="center">
                      Your infrastructure code passed all security checks.
                    </Typography>
                  </Box>
                )}
                
                {result.remediated_code && (
                  <Card sx={{ mt: 3 }}>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Remediated Code
                      </Typography>
                      <Typography variant="body2" paragraph>
                        Here's an improved version of your code with security issues fixed:
                      </Typography>
                      <Box sx={{ maxHeight: '300px', overflow: 'auto', borderRadius: 1, mb: 2 }}>
                        <SyntaxHighlighter
                          language={formData.iac_type === 'terraform' ? 'hcl' : formData.iac_type === 'ansible' ? 'yaml' : 'groovy'}
                          style={tomorrow}
                          showLineNumbers
                        >
                          {result.remediated_code}
                        </SyntaxHighlighter>
                      </Box>
                      <Button
                        variant="outlined"
                        size="small"
                        onClick={() => {
                          copyToClipboard(result.remediated_code);
                        }}
                      >
                        Copy to Clipboard
                      </Button>
                    </CardContent>
                  </Card>
                )}
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>
      
      <Snackbar
        open={showBackgroundProcessingAlert}
        autoHideDuration={10000}
        onClose={() => setShowBackgroundProcessingAlert(false)}
        message="Your request is being processed in the background. Check task history for results."
        action={
          <Button 
            color="primary" 
            size="small" 
            onClick={handleViewTaskHistory}
          >
            View Tasks
          </Button>
        }
      />
    </Box>
  );
}

export default SecurityReview; 