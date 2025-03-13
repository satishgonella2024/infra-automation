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
  Stepper,
  Step,
  StepLabel,
  Card,
  CardContent,
  Divider,
  Snackbar
} from '@mui/material';
import { 
  Code as CodeIcon,
  Send as SendIcon,
  Check as CheckIcon,
  History as HistoryIcon
} from '@mui/icons-material';
import { generateInfrastructure } from '../services/api';
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

function InfrastructureGenerator() {
  const navigate = useNavigate();
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [formData, setFormData] = useState({
    task: '',
    requirements: '',
    cloud_provider: 'aws',
    iac_type: 'terraform'
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

  const steps = ['Define Requirements', 'Generate Infrastructure', 'Review Results'];

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
      // Format requirements as JSON if it's a valid JSON string
      let formattedData = { ...formData };
      if (formData.requirements) {
        try {
          formattedData.requirements = JSON.parse(formData.requirements);
        } catch (err) {
          // If not valid JSON, keep as string
          formattedData.requirements = { description: formData.requirements };
        }
      } else {
        formattedData.requirements = {};
      }

      const response = await generateInfrastructure(formattedData);
      setResult(response);
      setTaskId(response.task_id);
      setActiveStep(2); // Move to review step
    } catch (err) {
      console.error('Failed to generate infrastructure:', err);
      let errorMessage = 'Failed to generate infrastructure. Please try again later.';
      
      // Provide more specific error messages based on the error
      if (err.code === 'ECONNABORTED') {
        errorMessage = 'The request timed out. Infrastructure generation is taking longer than expected. The system will continue processing your request in the background.';
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

  const handleNext = () => {
    setActiveStep((prevStep) => prevStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevStep) => prevStep - 1);
  };

  const handleReset = () => {
    setActiveStep(0);
    setResult(null);
    setFormData({
      task: '',
      requirements: '',
      cloud_provider: 'aws',
      iac_type: 'terraform'
    });
  };

  const handleViewTaskHistory = () => {
    navigate('/tasks');
  };

  const renderStepContent = (step) => {
    switch (step) {
      case 0:
        return (
          <Box component="form" onSubmit={(e) => { e.preventDefault(); handleNext(); }}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TextField
                  required
                  fullWidth
                  label="Task Description"
                  name="task"
                  value={formData.task}
                  onChange={handleInputChange}
                  placeholder="Describe what infrastructure you need, e.g., 'Create a highly available web application with a database'"
                  multiline
                  rows={3}
                />
              </Grid>
              
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Specific Requirements (Optional)"
                  name="requirements"
                  value={formData.requirements}
                  onChange={handleInputChange}
                  placeholder="Add any specific requirements as text or JSON, e.g., {'instances': 3, 'region': 'us-west-2'}"
                  multiline
                  rows={4}
                  helperText="You can provide requirements as plain text or JSON format"
                />
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
              
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel id="iac-type-label">Infrastructure as Code Type</InputLabel>
                  <Select
                    labelId="iac-type-label"
                    name="iac_type"
                    value={formData.iac_type}
                    label="Infrastructure as Code Type"
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
              
              <Grid item xs={12} sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleNext}
                  disabled={!formData.task}
                >
                  Next
                </Button>
              </Grid>
            </Grid>
          </Box>
        );
      
      case 1:
        return (
          <Box>
            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Review Your Request
              </Typography>
              
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <Typography variant="subtitle1">Task Description:</Typography>
                  <Typography variant="body1" sx={{ mb: 2 }}>
                    {formData.task}
                  </Typography>
                </Grid>
                
                {formData.requirements && (
                  <Grid item xs={12}>
                    <Typography variant="subtitle1">Specific Requirements:</Typography>
                    <Typography variant="body1" sx={{ mb: 2 }}>
                      {formData.requirements}
                    </Typography>
                  </Grid>
                )}
                
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle1">Cloud Provider:</Typography>
                  <Typography variant="body1" sx={{ mb: 2 }}>
                    {cloudProviders.find(p => p.value === formData.cloud_provider)?.label}
                  </Typography>
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle1">IaC Type:</Typography>
                  <Typography variant="body1" sx={{ mb: 2 }}>
                    {iacTypes.find(t => t.value === formData.iac_type)?.label}
                  </Typography>
                </Grid>
              </Grid>
            </Paper>
            
            {loading ? (
              <Box sx={{ my: 4 }}>
                <LoadingIndicator 
                  message="Generating infrastructure code..." 
                  showProgress={true}
                  timeout={180} // 3 minutes timeout
                />
                <Typography variant="body2" color="text.secondary" sx={{ mt: 2, textAlign: 'center' }}>
                  We're using AI to generate your infrastructure code. This may take a few minutes for complex requests.
                </Typography>
              </Box>
            ) : (
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Button onClick={handleBack}>
                  Back
                </Button>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleSubmit}
                  startIcon={<SendIcon />}
                >
                  Generate Infrastructure
                </Button>
              </Box>
            )}
            
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
                Your infrastructure generation request is being processed in the background. You can check the task history to see the results when it's complete.
              </Alert>
            )}
          </Box>
        );
      
      case 2:
        return (
          <Box>
            {result && (
              <>
                <Grid container spacing={3}>
                  <Grid item xs={12}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          Generated Infrastructure Code
                        </Typography>
                        <Box sx={{ maxHeight: '400px', overflow: 'auto', borderRadius: 1, mb: 2 }}>
                          <SyntaxHighlighter
                            language={formData.iac_type === 'terraform' ? 'hcl' : formData.iac_type === 'ansible' ? 'yaml' : 'groovy'}
                            style={tomorrow}
                            showLineNumbers
                          >
                            {result.code}
                          </SyntaxHighlighter>
                        </Box>
                        <Button
                          variant="outlined"
                          size="small"
                          onClick={() => {
                            copyToClipboard(result.code);
                          }}
                        >
                          Copy to Clipboard
                        </Button>
                      </CardContent>
                    </Card>
                  </Grid>
                  
                  {result.architecture_findings && Object.keys(result.architecture_findings).length > 0 && (
                    <Grid item xs={12} md={6}>
                      <Card>
                        <CardContent>
                          <Typography variant="h6" gutterBottom>
                            Architecture Review
                          </Typography>
                          <Typography variant="body2">
                            {JSON.stringify(result.architecture_findings, null, 2)}
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                  )}
                  
                  {result.security_findings && Object.keys(result.security_findings).length > 0 && (
                    <Grid item xs={12} md={6}>
                      <Card>
                        <CardContent>
                          <Typography variant="h6" gutterBottom>
                            Security Review
                          </Typography>
                          <Typography variant="body2">
                            {JSON.stringify(result.security_findings, null, 2)}
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                  )}
                  
                  {result.thoughts && (
                    <Grid item xs={12}>
                      <Card>
                        <CardContent>
                          <Typography variant="h6" gutterBottom>
                            Agent's Thought Process
                          </Typography>
                          <Typography variant="body2">
                            {result.thoughts}
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                  )}
                </Grid>
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
                  <Button onClick={handleReset}>
                    Generate New Infrastructure
                  </Button>
                </Box>
              </>
            )}
          </Box>
        );
      
      default:
        return null;
    }
  };

  return (
    <Box className="slide-in-up">
      <Typography variant="h4" component="h1" gutterBottom>
        Infrastructure Generator
      </Typography>
      <Typography variant="body1" paragraph>
        Generate infrastructure code using AI-powered automation.
      </Typography>
      
      <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>
      
      <Paper sx={{ p: 3 }}>
        {renderStepContent(activeStep)}
      </Paper>
      
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

export default InfrastructureGenerator; 