import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Switch,
  FormControlLabel,
  TextField,
  Button,
  Divider,
  Card,
  CardContent,
  Alert,
  Snackbar,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider,
  Tooltip,
  IconButton
} from '@mui/material';
import {
  DarkMode as DarkModeIcon,
  LightMode as LightModeIcon,
  Save as SaveIcon,
  Refresh as RefreshIcon,
  Help as HelpIcon
} from '@mui/icons-material';

function Settings() {
  const [settings, setSettings] = useState({
    darkMode: false,
    apiUrl: 'http://localhost:8000',
    refreshInterval: 30,
    defaultCloudProvider: 'aws',
    defaultIacType: 'terraform',
    showAgentThoughts: true,
    enableNotifications: true,
    maxHistoryItems: 50
  });

  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'success'
  });

  const handleSettingChange = (setting, value) => {
    setSettings({
      ...settings,
      [setting]: value
    });
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setSettings({
      ...settings,
      [name]: value
    });
  };

  const handleSwitchChange = (e) => {
    const { name, checked } = e.target;
    setSettings({
      ...settings,
      [name]: checked
    });
  };

  const handleSliderChange = (name) => (e, value) => {
    setSettings({
      ...settings,
      [name]: value
    });
  };

  const handleSaveSettings = () => {
    // In a real app, this would save to localStorage or an API
    localStorage.setItem('appSettings', JSON.stringify(settings));
    setSnackbar({
      open: true,
      message: 'Settings saved successfully!',
      severity: 'success'
    });
  };

  const handleResetSettings = () => {
    const defaultSettings = {
      darkMode: false,
      apiUrl: 'http://localhost:8000',
      refreshInterval: 30,
      defaultCloudProvider: 'aws',
      defaultIacType: 'terraform',
      showAgentThoughts: true,
      enableNotifications: true,
      maxHistoryItems: 50
    };
    setSettings(defaultSettings);
    setSnackbar({
      open: true,
      message: 'Settings reset to defaults',
      severity: 'info'
    });
  };

  const handleCloseSnackbar = () => {
    setSnackbar({
      ...snackbar,
      open: false
    });
  };

  return (
    <Box className="slide-in-up">
      <Typography variant="h4" component="h1" gutterBottom>
        Settings
      </Typography>
      <Typography variant="body1" paragraph>
        Configure application settings and preferences.
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Appearance
              </Typography>
              <Box sx={{ mb: 3 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.darkMode}
                      onChange={handleSwitchChange}
                      name="darkMode"
                      color="primary"
                    />
                  }
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      {settings.darkMode ? <DarkModeIcon sx={{ mr: 1 }} /> : <LightModeIcon sx={{ mr: 1 }} />}
                      {settings.darkMode ? 'Dark Mode' : 'Light Mode'}
                    </Box>
                  }
                />
              </Box>
              
              <Divider sx={{ my: 2 }} />
              
              <Typography variant="h6" gutterBottom>
                API Configuration
              </Typography>
              <TextField
                fullWidth
                label="API URL"
                name="apiUrl"
                value={settings.apiUrl}
                onChange={handleInputChange}
                margin="normal"
                helperText="The base URL for the infrastructure automation API"
              />
              
              <Box sx={{ mt: 2 }}>
                <Typography id="refresh-interval-slider" gutterBottom>
                  Dashboard Refresh Interval (seconds)
                </Typography>
                <Grid container spacing={2} alignItems="center">
                  <Grid item xs>
                    <Slider
                      value={settings.refreshInterval}
                      onChange={handleSliderChange('refreshInterval')}
                      aria-labelledby="refresh-interval-slider"
                      valueLabelDisplay="auto"
                      step={5}
                      marks
                      min={5}
                      max={60}
                    />
                  </Grid>
                  <Grid item>
                    <Typography>{settings.refreshInterval}s</Typography>
                  </Grid>
                </Grid>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Default Settings
              </Typography>
              
              <FormControl fullWidth margin="normal">
                <InputLabel id="default-cloud-provider-label">Default Cloud Provider</InputLabel>
                <Select
                  labelId="default-cloud-provider-label"
                  name="defaultCloudProvider"
                  value={settings.defaultCloudProvider}
                  label="Default Cloud Provider"
                  onChange={handleInputChange}
                >
                  <MenuItem value="aws">Amazon Web Services (AWS)</MenuItem>
                  <MenuItem value="azure">Microsoft Azure</MenuItem>
                  <MenuItem value="gcp">Google Cloud Platform (GCP)</MenuItem>
                </Select>
              </FormControl>
              
              <FormControl fullWidth margin="normal">
                <InputLabel id="default-iac-type-label">Default IaC Type</InputLabel>
                <Select
                  labelId="default-iac-type-label"
                  name="defaultIacType"
                  value={settings.defaultIacType}
                  label="Default IaC Type"
                  onChange={handleInputChange}
                >
                  <MenuItem value="terraform">Terraform</MenuItem>
                  <MenuItem value="ansible">Ansible</MenuItem>
                  <MenuItem value="jenkins">Jenkins</MenuItem>
                </Select>
              </FormControl>
              
              <Divider sx={{ my: 2 }} />
              
              <Typography variant="h6" gutterBottom>
                User Experience
              </Typography>
              
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.showAgentThoughts}
                    onChange={handleSwitchChange}
                    name="showAgentThoughts"
                    color="primary"
                  />
                }
                label="Show Agent Thoughts"
              />
              
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.enableNotifications}
                    onChange={handleSwitchChange}
                    name="enableNotifications"
                    color="primary"
                  />
                }
                label="Enable Notifications"
              />
              
              <Box sx={{ mt: 2 }}>
                <Typography id="max-history-slider" gutterBottom>
                  Maximum History Items
                </Typography>
                <Grid container spacing={2} alignItems="center">
                  <Grid item xs>
                    <Slider
                      value={settings.maxHistoryItems}
                      onChange={handleSliderChange('maxHistoryItems')}
                      aria-labelledby="max-history-slider"
                      valueLabelDisplay="auto"
                      step={10}
                      marks
                      min={10}
                      max={100}
                    />
                  </Grid>
                  <Grid item>
                    <Typography>{settings.maxHistoryItems}</Typography>
                  </Grid>
                </Grid>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12}>
          <Paper sx={{ p: 3, display: 'flex', justifyContent: 'space-between' }}>
            <Button
              variant="outlined"
              color="secondary"
              startIcon={<RefreshIcon />}
              onClick={handleResetSettings}
            >
              Reset to Defaults
            </Button>
            <Button
              variant="contained"
              color="primary"
              startIcon={<SaveIcon />}
              onClick={handleSaveSettings}
            >
              Save Settings
            </Button>
          </Paper>
        </Grid>
      </Grid>
      
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}

export default Settings; 