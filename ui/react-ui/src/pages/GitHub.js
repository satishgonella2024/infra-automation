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
  GitHub as GitHubIcon,
  Code as CodeIcon,
  MergeType as MergeIcon,
  BugReport as IssueIcon,
  PlayArrow as ActionIcon
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';

const GitHub = () => {
  const theme = useTheme();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [action, setAction] = useState('create_repository');
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    private: false,
    template: false,
    autoInit: true,
    gitignore_template: 'Node',
    license_template: 'mit'
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch('/api/github', {
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
        throw new Error(data.detail || 'Failed to process GitHub request');
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
    const { name, value, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: e.target.type === 'checkbox' ? checked : value
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
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.private}
                    onChange={handleChange}
                    name="private"
                  />
                }
                label="Private Repository"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.template}
                    onChange={handleChange}
                    name="template"
                  />
                }
                label="Template Repository"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.autoInit}
                    onChange={handleChange}
                    name="autoInit"
                  />
                }
                label="Initialize with README"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>GitIgnore Template</InputLabel>
                <Select
                  name="gitignore_template"
                  value={formData.gitignore_template}
                  label="GitIgnore Template"
                  onChange={handleChange}
                >
                  <MenuItem value="Node">Node</MenuItem>
                  <MenuItem value="Python">Python</MenuItem>
                  <MenuItem value="Java">Java</MenuItem>
                  <MenuItem value="Go">Go</MenuItem>
                  <MenuItem value="none">None</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>License Template</InputLabel>
                <Select
                  name="license_template"
                  value={formData.license_template}
                  label="License Template"
                  onChange={handleChange}
                >
                  <MenuItem value="mit">MIT</MenuItem>
                  <MenuItem value="apache-2.0">Apache 2.0</MenuItem>
                  <MenuItem value="gpl-3.0">GPL 3.0</MenuItem>
                  <MenuItem value="none">None</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </>
        );
      
      case 'create_pull_request':
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
                helperText="owner/repo format"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Title"
                name="title"
                value={formData.title}
                onChange={handleChange}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                name="description"
                value={formData.description}
                onChange={handleChange}
                multiline
                rows={4}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Base Branch"
                name="base"
                value={formData.base}
                onChange={handleChange}
                required
                defaultValue="main"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Head Branch"
                name="head"
                value={formData.head}
                onChange={handleChange}
                required
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
        <GitHubIcon fontSize="large" />
        GitHub Integration
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
                        <MenuItem value="create_pull_request">Create Pull Request</MenuItem>
                        <MenuItem value="review_code">Review Code</MenuItem>
                        <MenuItem value="generate_workflow">Generate GitHub Actions Workflow</MenuItem>
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
                  <CodeIcon />
                </ListItemIcon>
                <ListItemText 
                  primary="Created repository: my-project"
                  secondary="2 hours ago"
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <MergeIcon />
                </ListItemIcon>
                <ListItemText 
                  primary="Merged PR: Update README"
                  secondary="3 hours ago"
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <ActionIcon />
                </ListItemIcon>
                <ListItemText 
                  primary="Generated workflow: CI/CD"
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

export default GitHub; 