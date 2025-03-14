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
  Switch,
  FormControlLabel
} from '@mui/material';
import {
  CloudSync as ArgoCDIcon,
  Sync as SyncIcon,
  History as HistoryIcon,
  Settings as SettingsIcon,
  CheckCircle as HealthyIcon,
  Error as UnhealthyIcon
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';

const ArgoCD = () => {
  const theme = useTheme();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [action, setAction] = useState('create_application');
  const [formData, setFormData] = useState({
    name: '',
    project: 'default',
    repoURL: '',
    path: '',
    targetRevision: 'HEAD',
    namespace: 'default',
    syncPolicy: {
      automated: false,
      prune: false,
      selfHeal: false
    }
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch('/api/argocd', {
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
        throw new Error(data.detail || 'Failed to process ArgoCD request');
      }

      setSuccess('Operation completed successfully');
      if (action === 'create_application') {
        setFormData({
          ...formData,
          name: '',
          repoURL: '',
          path: ''
        });
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value, checked } = e.target;
    if (name.startsWith('syncPolicy.')) {
      const policyKey = name.split('.')[1];
      setFormData(prev => ({
        ...prev,
        syncPolicy: {
          ...prev.syncPolicy,
          [policyKey]: checked
        }
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: value
      }));
    }
  };

  const renderFormFields = () => {
    switch (action) {
      case 'create_application':
        return (
          <>
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
                label="Project"
                name="project"
                value={formData.project}
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
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Repository URL"
                name="repoURL"
                value={formData.repoURL}
                onChange={handleChange}
                required
                helperText="Git repository URL containing your application manifests"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Path"
                name="path"
                value={formData.path}
                onChange={handleChange}
                required
                helperText="Path to the application manifests in the repository"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Target Revision"
                name="targetRevision"
                value={formData.targetRevision}
                onChange={handleChange}
                required
                helperText="Branch, tag, or commit hash"
              />
            </Grid>
            <Grid item xs={12}>
              <Typography variant="subtitle1" gutterBottom>
                Sync Policy
              </Typography>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.syncPolicy.automated}
                    onChange={handleChange}
                    name="syncPolicy.automated"
                  />
                }
                label="Automated Sync"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.syncPolicy.prune}
                    onChange={handleChange}
                    name="syncPolicy.prune"
                  />
                }
                label="Prune Resources"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.syncPolicy.selfHeal}
                    onChange={handleChange}
                    name="syncPolicy.selfHeal"
                  />
                }
                label="Self Heal"
              />
            </Grid>
          </>
        );

      case 'sync_application':
        return (
          <>
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
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.prune}
                    onChange={handleChange}
                    name="prune"
                  />
                }
                label="Prune Resources"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.dryRun}
                    onChange={handleChange}
                    name="dryRun"
                  />
                }
                label="Dry Run"
              />
            </Grid>
          </>
        );

      default:
        return null;
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <ArgoCDIcon fontSize="large" />
        ArgoCD Management
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <form onSubmit={handleSubmit}>
                <Grid container spacing={2}>
                  <Grid item xs={12}>
                    <FormControl fullWidth>
                      <InputLabel>Action</InputLabel>
                      <Select
                        value={action}
                        label="Action"
                        onChange={(e) => setAction(e.target.value)}
                      >
                        <MenuItem value="create_application">Create Application</MenuItem>
                        <MenuItem value="sync_application">Sync Application</MenuItem>
                        <MenuItem value="delete_application">Delete Application</MenuItem>
                        <MenuItem value="get_status">Get Application Status</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>

                  {renderFormFields()}

                  <Grid item xs={12}>
                    <Button
                      type="submit"
                      variant="contained"
                      fullWidth
                      disabled={loading}
                      sx={{ mt: 2 }}
                    >
                      {loading ? <CircularProgress size={24} /> : 'Submit'}
                    </Button>
                  </Grid>
                </Grid>
              </form>

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
              Application Status
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <List>
              <ListItem>
                <ListItemIcon>
                  <HealthyIcon color="success" />
                </ListItemIcon>
                <ListItemText 
                  primary="frontend-app"
                  secondary="Synced and healthy"
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <SyncIcon color="warning" />
                </ListItemIcon>
                <ListItemText 
                  primary="backend-api"
                  secondary="Out of sync"
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <UnhealthyIcon color="error" />
                </ListItemIcon>
                <ListItemText 
                  primary="database"
                  secondary="Degraded"
                />
              </ListItem>
            </List>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ArgoCD; 