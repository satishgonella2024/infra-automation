import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  TextField,
  Button,
  Card,
  CardContent,
  Grid,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  Paper,
  Divider,
  CircularProgress,
  Alert,
  Stepper,
  Step,
  StepLabel,
  Chip
} from '@mui/material';
import {
  Storage as StorageIcon,
  Code as CodeIcon,
  Description as DescriptionIcon,
  CloudQueue as CloudIcon,
  Category as CategoryIcon
} from '@mui/icons-material';
import LoadingIndicator from '../components/LoadingIndicator';

const TerraformModules = () => {
  const navigate = useNavigate();
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [taskId, setTaskId] = useState(null);
  
  // Form state
  const [formData, setFormData] = useState({
    task: '',
    requirements: '',
    cloud_provider: 'aws',
    module_type: 'compute',
    module_name: ''
  });
  
  const cloudProviders = [
    { value: 'aws', label: 'Amazon Web Services (AWS)' },
    { value: 'azure', label: 'Microsoft Azure' },
    { value: 'gcp', label: 'Google Cloud Platform (GCP)' }
  ];
  
  const moduleTypes = [
    { value: 'networking', label: 'Networking' },
    { value: 'compute', label: 'Compute' },
    { value: 'storage', label: 'Storage' },
    { value: 'security', label: 'Security' }
  ];
  
  const steps = [
    'Define Requirements',
    'Configure Module',
    'Generate Module'
  ];
  
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  const handleNext = () => {
    setActiveStep(prevStep => prevStep + 1);
  };
  
  const handleBack = () => {
    setActiveStep(prevStep => prevStep - 1);
  };
  
  const handleSubmit = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Format requirements as JSON if it's a string
      let parsedRequirements = formData.requirements;
      if (typeof formData.requirements === 'string') {
        try {
          parsedRequirements = JSON.parse(formData.requirements);
        } catch (e) {
          // If not valid JSON, treat as a string
          parsedRequirements = { description: formData.requirements };
        }
      }
      
      const requestData = {
        task: formData.task,
        requirements: parsedRequirements,
        cloud_provider: formData.cloud_provider,
        module_type: formData.module_type,
        module_name: formData.module_name || undefined
      };
      
      const response = await fetch('http://localhost:8000/terraform/module', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setTaskId(data.task_id);
        setSuccess(true);
        setActiveStep(3); // Move to completion step
      } else {
        throw new Error(data.detail || 'Failed to generate Terraform module');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  const renderStepContent = (step) => {
    switch (step) {
      case 0:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Define Your Module Requirements
            </Typography>
            <TextField
              fullWidth
              label="Module Description"
              name="task"
              value={formData.task}
              onChange={handleChange}
              margin="normal"
              multiline
              rows={3}
              placeholder="Describe what you want the module to do, e.g., 'Create a reusable AWS VPC module with public and private subnets'"
              required
            />
            <TextField
              fullWidth
              label="Detailed Requirements"
              name="requirements"
              value={formData.requirements}
              onChange={handleChange}
              margin="normal"
              multiline
              rows={6}
              placeholder="Provide detailed requirements in JSON format or plain text. Example: { 'vpc_cidr': '10.0.0.0/16', 'enable_nat_gateway': true }"
              required
            />
          </Box>
        );
      case 1:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Configure Module Settings
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth margin="normal">
                  <InputLabel>Cloud Provider</InputLabel>
                  <Select
                    name="cloud_provider"
                    value={formData.cloud_provider}
                    onChange={handleChange}
                    label="Cloud Provider"
                  >
                    {cloudProviders.map(provider => (
                      <MenuItem key={provider.value} value={provider.value}>
                        {provider.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth margin="normal">
                  <InputLabel>Module Type</InputLabel>
                  <Select
                    name="module_type"
                    value={formData.module_type}
                    onChange={handleChange}
                    label="Module Type"
                  >
                    {moduleTypes.map(type => (
                      <MenuItem key={type.value} value={type.value}>
                        {type.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Module Name (Optional)"
                  name="module_name"
                  value={formData.module_name}
                  onChange={handleChange}
                  margin="normal"
                  placeholder="Leave blank for auto-generated name"
                  helperText="Custom name for your module, e.g., terraform-aws-vpc-multi-az"
                />
              </Grid>
            </Grid>
          </Box>
        );
      case 2:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Review and Generate
            </Typography>
            <Paper sx={{ p: 3, mb: 3 }}>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <DescriptionIcon sx={{ mr: 1, color: 'primary.main' }} />
                    <Typography variant="subtitle1">Module Description</Typography>
                  </Box>
                  <Typography variant="body1" sx={{ ml: 4 }}>
                    {formData.task}
                  </Typography>
                </Grid>
                
                <Grid item xs={12}>
                  <Divider sx={{ my: 2 }} />
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <CloudIcon sx={{ mr: 1, color: 'primary.main' }} />
                    <Typography variant="subtitle1">Cloud Provider</Typography>
                  </Box>
                  <Chip 
                    label={cloudProviders.find(p => p.value === formData.cloud_provider)?.label} 
                    sx={{ ml: 4 }}
                  />
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <CategoryIcon sx={{ mr: 1, color: 'primary.main' }} />
                    <Typography variant="subtitle1">Module Type</Typography>
                  </Box>
                  <Chip 
                    label={moduleTypes.find(t => t.value === formData.module_type)?.label} 
                    sx={{ ml: 4 }}
                  />
                </Grid>
                
                {formData.module_name && (
                  <Grid item xs={12}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <StorageIcon sx={{ mr: 1, color: 'primary.main' }} />
                      <Typography variant="subtitle1">Module Name</Typography>
                    </Box>
                    <Typography variant="body1" sx={{ ml: 4 }}>
                      {formData.module_name}
                    </Typography>
                  </Grid>
                )}
                
                <Grid item xs={12}>
                  <Divider sx={{ my: 2 }} />
                </Grid>
                
                <Grid item xs={12}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <CodeIcon sx={{ mr: 1, color: 'primary.main' }} />
                    <Typography variant="subtitle1">Requirements</Typography>
                  </Box>
                  <Paper 
                    variant="outlined" 
                    sx={{ 
                      p: 2, 
                      ml: 4, 
                      backgroundColor: 'grey.50',
                      maxHeight: '200px',
                      overflow: 'auto'
                    }}
                  >
                    <pre style={{ margin: 0 }}>
                      {formData.requirements}
                    </pre>
                  </Paper>
                </Grid>
              </Grid>
            </Paper>
            
            {error && (
              <Alert severity="error" sx={{ mb: 3 }}>
                {error}
              </Alert>
            )}
            
            <Box sx={{ display: 'flex', justifyContent: 'center' }}>
              <Button
                variant="contained"
                color="primary"
                size="large"
                onClick={handleSubmit}
                disabled={loading}
                startIcon={loading ? <CircularProgress size={20} /> : <StorageIcon />}
              >
                {loading ? 'Generating...' : 'Generate Terraform Module'}
              </Button>
            </Box>
          </Box>
        );
      case 3:
        return (
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h6" gutterBottom>
              Module Generation Started
            </Typography>
            
            {loading ? (
              <LoadingIndicator message="Generating your Terraform module..." />
            ) : (
              <>
                <Alert severity="success" sx={{ mb: 3 }}>
                  Your Terraform module generation has been started successfully!
                </Alert>
                
                <Typography variant="body1" paragraph>
                  Task ID: <strong>{taskId}</strong>
                </Typography>
                
                <Typography variant="body1" paragraph>
                  You can view the status and download the generated module from the Tasks page.
                </Typography>
                
                <Paper sx={{ p: 3, mb: 3, textAlign: 'left' }}>
                  <Typography variant="h6" gutterBottom>
                    What to expect:
                  </Typography>
                  <Box component="ul" sx={{ pl: 2 }}>
                    <Box component="li" sx={{ mb: 1 }}>
                      <Typography variant="body1">
                        <strong>Modular Structure:</strong> The generated Terraform module will follow best practices with a modular structure.
                      </Typography>
                    </Box>
                    <Box component="li" sx={{ mb: 1 }}>
                      <Typography variant="body1">
                        <strong>File Tree View:</strong> You'll be able to browse the module's file structure in a tree view.
                      </Typography>
                    </Box>
                    <Box component="li" sx={{ mb: 1 }}>
                      <Typography variant="body1">
                        <strong>Download as ZIP:</strong> The complete module can be downloaded as a ZIP file for easy integration into your projects.
                      </Typography>
                    </Box>
                    <Box component="li">
                      <Typography variant="body1">
                        <strong>Documentation:</strong> The module includes README.md with usage instructions and examples.
                      </Typography>
                    </Box>
                  </Box>
                </Paper>
                
                <Box sx={{ mt: 4, display: 'flex', justifyContent: 'center', gap: 2 }}>
                  <Button
                    variant="contained"
                    color="primary"
                    onClick={() => navigate(`/tasks?id=${taskId}`)}
                  >
                    View Task
                  </Button>
                  
                  <Button
                    variant="outlined"
                    onClick={() => {
                      setActiveStep(0);
                      setFormData({
                        task: '',
                        requirements: '',
                        cloud_provider: 'aws',
                        module_type: 'compute',
                        module_name: ''
                      });
                      setTaskId(null);
                      setSuccess(false);
                    }}
                  >
                    Create Another Module
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
    <Box className="slide-in-up" sx={{ p: 3 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Enterprise Terraform Modules
      </Typography>
      
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <StorageIcon sx={{ fontSize: 40, color: 'success.main', mr: 2 }} />
            <Box>
              <Typography variant="h5">
                Create Enterprise-Grade Terraform Modules
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Generate production-ready, reusable Terraform modules following best practices
              </Typography>
            </Box>
          </Box>
          
          <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>
          
          {renderStepContent(activeStep)}
          
          {activeStep < 3 && (
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
              <Button
                disabled={activeStep === 0}
                onClick={handleBack}
              >
                Back
              </Button>
              
              <Button
                variant="contained"
                onClick={activeStep === 2 ? handleSubmit : handleNext}
                disabled={
                  (activeStep === 0 && (!formData.task || !formData.requirements)) ||
                  loading
                }
              >
                {activeStep === 2 ? 'Generate' : 'Next'}
              </Button>
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default TerraformModules; 