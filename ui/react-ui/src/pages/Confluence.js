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
  ListItemIcon
} from '@mui/material';
import {
  Description as ConfluenceIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Folder as SpaceIcon
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';

const Confluence = () => {
  const theme = useTheme();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [action, setAction] = useState('create_page');
  const [formData, setFormData] = useState({
    spaceKey: '',
    title: '',
    content: '',
    parentId: '',
    labels: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch('/api/confluence', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          action,
          parameters: {
            ...formData,
            labels: formData.labels.split(',').map(label => label.trim()).filter(Boolean)
          }
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to process Confluence request');
      }

      setSuccess('Operation completed successfully');
      if (action === 'create_page') {
        setFormData({
          ...formData,
          title: '',
          content: ''
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

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <ConfluenceIcon fontSize="large" />
        Confluence Integration
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
                        <MenuItem value="create_page">Create Page</MenuItem>
                        <MenuItem value="update_page">Update Page</MenuItem>
                        <MenuItem value="create_space">Create Space</MenuItem>
                        <MenuItem value="generate_documentation">Generate Documentation</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>

                  {action !== 'generate_documentation' && (
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label="Space Key"
                        name="spaceKey"
                        value={formData.spaceKey}
                        onChange={handleChange}
                        required
                        helperText="The key of the Confluence space"
                      />
                    </Grid>
                  )}

                  {(action === 'create_page' || action === 'update_page') && (
                    <>
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
                          label="Content"
                          name="content"
                          value={formData.content}
                          onChange={handleChange}
                          multiline
                          rows={8}
                          required
                          helperText="You can use Markdown syntax"
                        />
                      </Grid>

                      <Grid item xs={12}>
                        <TextField
                          fullWidth
                          label="Parent Page ID"
                          name="parentId"
                          value={formData.parentId}
                          onChange={handleChange}
                          helperText="Optional: ID of the parent page"
                        />
                      </Grid>

                      <Grid item xs={12}>
                        <TextField
                          fullWidth
                          label="Labels"
                          name="labels"
                          value={formData.labels}
                          onChange={handleChange}
                          helperText="Comma-separated list of labels"
                        />
                      </Grid>
                    </>
                  )}

                  {action === 'generate_documentation' && (
                    <Grid item xs={12}>
                      <Alert severity="info" sx={{ mb: 2 }}>
                        This will analyze your infrastructure code and generate comprehensive documentation in Confluence.
                      </Alert>
                      <TextField
                        fullWidth
                        label="Target Directory"
                        name="targetDirectory"
                        value={formData.targetDirectory}
                        onChange={handleChange}
                        required
                        helperText="Path to the infrastructure code directory"
                      />
                    </Grid>
                  )}

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
              Recent Pages
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <List>
              {/* Add recent pages list here */}
              <ListItem>
                <ListItemIcon>
                  <ConfluenceIcon />
                </ListItemIcon>
                <ListItemText 
                  primary="Sample Page"
                  secondary="Last updated: 2 hours ago"
                />
              </ListItem>
            </List>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Confluence; 