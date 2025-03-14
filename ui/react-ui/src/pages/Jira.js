import React, { useState, useEffect } from 'react';
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
  Chip,
  CircularProgress,
  Alert,
  Paper,
  Divider
} from '@mui/material';
import { Assignment as JiraIcon } from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';

const Jira = () => {
  const theme = useTheme();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [action, setAction] = useState('create_issue');
  const [formData, setFormData] = useState({
    project: '',
    summary: '',
    description: '',
    issueType: 'Task',
    priority: 'Medium'
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch('/api/jira', {
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
        throw new Error(data.detail || 'Failed to process Jira request');
      }

      setSuccess('Operation completed successfully');
      // Reset form if needed
      if (action === 'create_issue') {
        setFormData({
          ...formData,
          summary: '',
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

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <JiraIcon fontSize="large" />
        Jira Integration
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
                        <MenuItem value="create_issue">Create Issue</MenuItem>
                        <MenuItem value="update_issue">Update Issue</MenuItem>
                        <MenuItem value="search_issues">Search Issues</MenuItem>
                        <MenuItem value="create_epic">Create Epic</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>

                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Project"
                      name="project"
                      value={formData.project}
                      onChange={handleChange}
                      required
                    />
                  </Grid>

                  {action !== 'search_issues' && (
                    <>
                      <Grid item xs={12}>
                        <TextField
                          fullWidth
                          label="Summary"
                          name="summary"
                          value={formData.summary}
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
                        <FormControl fullWidth>
                          <InputLabel>Issue Type</InputLabel>
                          <Select
                            name="issueType"
                            value={formData.issueType}
                            label="Issue Type"
                            onChange={handleChange}
                          >
                            <MenuItem value="Task">Task</MenuItem>
                            <MenuItem value="Story">Story</MenuItem>
                            <MenuItem value="Bug">Bug</MenuItem>
                            <MenuItem value="Epic">Epic</MenuItem>
                          </Select>
                        </FormControl>
                      </Grid>

                      <Grid item xs={12} sm={6}>
                        <FormControl fullWidth>
                          <InputLabel>Priority</InputLabel>
                          <Select
                            name="priority"
                            value={formData.priority}
                            label="Priority"
                            onChange={handleChange}
                          >
                            <MenuItem value="Highest">Highest</MenuItem>
                            <MenuItem value="High">High</MenuItem>
                            <MenuItem value="Medium">Medium</MenuItem>
                            <MenuItem value="Low">Low</MenuItem>
                            <MenuItem value="Lowest">Lowest</MenuItem>
                          </Select>
                        </FormControl>
                      </Grid>
                    </>
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
              Recent Activity
            </Typography>
            <Divider sx={{ mb: 2 }} />
            {/* Add recent activity list here */}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Jira; 