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
  Cloud as NexusIcon,
  Storage as RepositoryIcon,
  Upload as UploadIcon,
  Delete as DeleteIcon,
  Search as SearchIcon
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';

const Nexus = () => {
  const theme = useTheme();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [action, setAction] = useState('create_repository');
  const [formData, setFormData] = useState({
    name: '',
    format: 'maven2',
    type: 'hosted',
    description: '',
    cleanup_policy: '',
    blob_store: 'default'
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch('/api/nexus', {
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
        throw new Error(data.detail || 'Failed to process Nexus request');
      }

      setSuccess('Operation completed successfully');
      if (action === 'create_repository') {
        setFormData({
          ...formData,
          name: '',
          description: ''
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
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const renderFormFields = () => {
    switch (action) {
      case 'create_repository':
        return (
          <>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Repository Name"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Format</InputLabel>
                <Select
                  name="format"
                  value={formData.format}
                  label="Format"
                  onChange={handleChange}
                >
                  <MenuItem value="maven2">Maven2</MenuItem>
                  <MenuItem value="npm">npm</MenuItem>
                  <MenuItem value="docker">Docker</MenuItem>
                  <MenuItem value="raw">Raw</MenuItem>
                  <MenuItem value="pypi">PyPI</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Type</InputLabel>
                <Select
                  name="type"
                  value={formData.type}
                  label="Type"
                  onChange={handleChange}
                >
                  <MenuItem value="hosted">Hosted</MenuItem>
                  <MenuItem value="proxy">Proxy</MenuItem>
                  <MenuItem value="group">Group</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                name="description"
                value={formData.description}
                onChange={handleChange}
                multiline
                rows={3}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Cleanup Policy"
                name="cleanup_policy"
                value={formData.cleanup_policy}
                onChange={handleChange}
                helperText="Optional: Name of the cleanup policy"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Blob Store"
                name="blob_store"
                value={formData.blob_store}
                onChange={handleChange}
                defaultValue="default"
                helperText="Storage location for repository contents"
              />
            </Grid>
          </>
        );
      
      case 'upload_artifact':
        return (
          <>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Repository"
                name="repository"
                value={formData.repository}
                onChange={handleChange}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Group ID"
                name="group_id"
                value={formData.group_id}
                onChange={handleChange}
                required
                helperText="e.g., com.example"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Artifact ID"
                name="artifact_id"
                value={formData.artifact_id}
                onChange={handleChange}
                required
                helperText="e.g., my-project"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Version"
                name="version"
                value={formData.version}
                onChange={handleChange}
                required
                helperText="e.g., 1.0.0"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                type="file"
                label="File"
                name="file"
                onChange={handleChange}
                required
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
          </>
        );

      case 'search_artifacts':
        return (
          <>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Repository"
                name="repository"
                value={formData.repository}
                onChange={handleChange}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Search Query"
                name="query"
                value={formData.query}
                onChange={handleChange}
                required
                helperText="Search by name, group ID, or artifact ID"
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
        <NexusIcon fontSize="large" />
        Nexus Repository Manager
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
                        <MenuItem value="create_repository">Create Repository</MenuItem>
                        <MenuItem value="upload_artifact">Upload Artifact</MenuItem>
                        <MenuItem value="search_artifacts">Search Artifacts</MenuItem>
                        <MenuItem value="create_cleanup_policy">Create Cleanup Policy</MenuItem>
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
              Recent Activity
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <List>
              <ListItem>
                <ListItemIcon>
                  <RepositoryIcon />
                </ListItemIcon>
                <ListItemText 
                  primary="Created repository: maven-releases"
                  secondary="2 hours ago"
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <UploadIcon />
                </ListItemIcon>
                <ListItemText 
                  primary="Uploaded: my-project-1.0.0.jar"
                  secondary="3 hours ago"
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <DeleteIcon />
                </ListItemIcon>
                <ListItemText 
                  primary="Cleanup: Removed old snapshots"
                  secondary="5 hours ago"
                />
              </ListItem>
            </List>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Nexus; 