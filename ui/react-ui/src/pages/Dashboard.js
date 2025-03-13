import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Button,
  Card,
  CardContent,
  CardActions,
  Divider,
  LinearProgress,
  Chip,
  Stack,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Code as CodeIcon,
  Security as SecurityIcon,
  History as HistoryIcon,
  Visibility as VisibilityIcon,
  ArrowForward as ArrowForwardIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon
} from '@mui/icons-material';
import { fetchTasks } from '../services/api';
import { Chart as ChartJS, ArcElement, Tooltip as ChartTooltip, Legend } from 'chart.js';
import { Doughnut } from 'react-chartjs-2';

// Register Chart.js components
ChartJS.register(ArcElement, ChartTooltip, Legend);

function Dashboard({ apiStatus }) {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    total: 0,
    successful: 0,
    failed: 0,
    inProgress: 0
  });

  useEffect(() => {
    const loadTasks = async () => {
      try {
        setLoading(true);
        const data = await fetchTasks(5, 0);
        setTasks(data);
        
        // Calculate stats
        const total = data.length;
        const successful = data.filter(task => task.status === 'completed').length;
        const failed = data.filter(task => task.status === 'failed').length;
        const inProgress = data.filter(task => task.status === 'in_progress').length;
        
        setStats({
          total,
          successful,
          failed,
          inProgress
        });
      } catch (error) {
        console.error('Failed to fetch tasks:', error);
      } finally {
        setLoading(false);
      }
    };

    loadTasks();
  }, []);

  const handleRefresh = async () => {
    try {
      setLoading(true);
      const data = await fetchTasks(5, 0);
      setTasks(data);
    } catch (error) {
      console.error('Failed to refresh tasks:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon color="success" />;
      case 'failed':
        return <ErrorIcon color="error" />;
      case 'in_progress':
        return <WarningIcon color="warning" />;
      default:
        return null;
    }
  };

  const getTaskTypeIcon = (type) => {
    switch (type) {
      case 'infrastructure_generation':
        return <CodeIcon />;
      case 'security_review':
        return <SecurityIcon />;
      default:
        return <HistoryIcon />;
    }
  };

  const chartData = {
    labels: ['Successful', 'Failed', 'In Progress'],
    datasets: [
      {
        data: [stats.successful, stats.failed, stats.inProgress],
        backgroundColor: [
          '#4caf50', // success
          '#f44336', // error
          '#ff9800', // warning
        ],
        borderColor: [
          '#388e3c',
          '#d32f2f',
          '#f57c00',
        ],
        borderWidth: 1,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
      },
    },
  };

  return (
    <Box className="slide-in-up" sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Dashboard
        </Typography>
        <Button
          variant="contained"
          startIcon={<RefreshIcon />}
          onClick={handleRefresh}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      {/* Status Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={3}>
          <Paper
            elevation={0}
            sx={{
              p: 3,
              borderRadius: 2,
              boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
              height: '100%',
              border: '1px solid rgba(0,0,0,0.08)',
              transition: 'transform 0.3s ease-in-out, box-shadow 0.3s ease-in-out',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 8px 16px rgba(0,0,0,0.1)',
              },
            }}
          >
            <Typography variant="h6" gutterBottom>
              API Status
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', mt: 2 }}>
              <Chip
                label={apiStatus.status}
                color={apiStatus.status === 'online' ? 'success' : 'error'}
                sx={{ mr: 1 }}
              />
              <Typography variant="body2" color="text.secondary">
                {apiStatus.status === 'online' ? 'System is operational' : 'System is offline'}
              </Typography>
            </Box>
          </Paper>
        </Grid>
        <Grid item xs={12} md={3}>
          <Paper
            elevation={0}
            sx={{
              p: 3,
              borderRadius: 2,
              boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
              height: '100%',
              border: '1px solid rgba(0,0,0,0.08)',
              transition: 'transform 0.3s ease-in-out, box-shadow 0.3s ease-in-out',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 8px 16px rgba(0,0,0,0.1)',
              },
            }}
          >
            <Typography variant="h6" gutterBottom>
              Agents
            </Typography>
            <Stack spacing={1} sx={{ mt: 2 }}>
              {apiStatus.agents && apiStatus.agents.map((agent) => (
                <Box key={agent.name} sx={{ display: 'flex', alignItems: 'center' }}>
                  <Chip
                    size="small"
                    label={agent.status}
                    color={agent.status === 'idle' ? 'success' : agent.status === 'processing' ? 'warning' : 'error'}
                    sx={{ mr: 1 }}
                  />
                  <Typography variant="body2">
                    {agent.name}
                  </Typography>
                </Box>
              ))}
            </Stack>
          </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper
            elevation={0}
            sx={{
              p: 3,
              borderRadius: 2,
              boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
              height: '100%',
              border: '1px solid rgba(0,0,0,0.08)',
              transition: 'transform 0.3s ease-in-out, box-shadow 0.3s ease-in-out',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 8px 16px rgba(0,0,0,0.1)',
              },
            }}
          >
            <Typography variant="h6" gutterBottom>
              Task Statistics
            </Typography>
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12} md={7}>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2" color="text.secondary">Total Tasks</Typography>
                    <Typography variant="body1" fontWeight="medium">{stats.total}</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2" color="text.secondary">Successful</Typography>
                    <Typography variant="body1" fontWeight="medium" color="success.main">{stats.successful}</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2" color="text.secondary">Failed</Typography>
                    <Typography variant="body1" fontWeight="medium" color="error.main">{stats.failed}</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2" color="text.secondary">In Progress</Typography>
                    <Typography variant="body1" fontWeight="medium" color="warning.main">{stats.inProgress}</Typography>
                  </Box>
                </Box>
              </Grid>
              <Grid item xs={12} md={5}>
                <Box sx={{ height: 140 }}>
                  <Doughnut data={chartData} options={chartOptions} />
                </Box>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
      </Grid>

      {/* Quick Actions */}
      <Typography variant="h5" gutterBottom sx={{ mb: 2 }}>
        Quick Actions
      </Typography>
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card 
            sx={{ 
              height: '100%',
              transition: 'transform 0.3s ease-in-out, box-shadow 0.3s ease-in-out',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 8px 16px rgba(0,0,0,0.1)',
              },
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Box
                  sx={{
                    backgroundColor: 'primary.light',
                    borderRadius: '50%',
                    p: 1,
                    mr: 2,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <CodeIcon sx={{ color: 'primary.main' }} />
                </Box>
                <Typography variant="h6">
                  Generate Infrastructure
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Create new infrastructure using AI-powered automation
              </Typography>
            </CardContent>
            <CardActions>
              <Button 
                size="small" 
                endIcon={<ArrowForwardIcon />}
                onClick={() => navigate('/generate')}
              >
                Start
              </Button>
            </CardActions>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card 
            sx={{ 
              height: '100%',
              transition: 'transform 0.3s ease-in-out, box-shadow 0.3s ease-in-out',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 8px 16px rgba(0,0,0,0.1)',
              },
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Box
                  sx={{
                    backgroundColor: 'error.light',
                    borderRadius: '50%',
                    p: 1,
                    mr: 2,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <SecurityIcon sx={{ color: 'error.main' }} />
                </Box>
                <Typography variant="h6">
                  Security Review
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Analyze your infrastructure for security vulnerabilities
              </Typography>
            </CardContent>
            <CardActions>
              <Button 
                size="small" 
                endIcon={<ArrowForwardIcon />}
                onClick={() => navigate('/security')}
              >
                Review
              </Button>
            </CardActions>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card 
            sx={{ 
              height: '100%',
              transition: 'transform 0.3s ease-in-out, box-shadow 0.3s ease-in-out',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 8px 16px rgba(0,0,0,0.1)',
              },
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Box
                  sx={{
                    backgroundColor: 'info.light',
                    borderRadius: '50%',
                    p: 1,
                    mr: 2,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <VisibilityIcon sx={{ color: 'info.main' }} />
                </Box>
                <Typography variant="h6">
                  Visualize
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                View graphical representations of your infrastructure
              </Typography>
            </CardContent>
            <CardActions>
              <Button 
                size="small" 
                endIcon={<ArrowForwardIcon />}
                onClick={() => navigate('/visualization')}
              >
                View
              </Button>
            </CardActions>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card 
            sx={{ 
              height: '100%',
              transition: 'transform 0.3s ease-in-out, box-shadow 0.3s ease-in-out',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 8px 16px rgba(0,0,0,0.1)',
              },
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Box
                  sx={{
                    backgroundColor: 'warning.light',
                    borderRadius: '50%',
                    p: 1,
                    mr: 2,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <HistoryIcon sx={{ color: 'warning.main' }} />
                </Box>
                <Typography variant="h6">
                  Task History
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                View and manage your past infrastructure tasks
              </Typography>
            </CardContent>
            <CardActions>
              <Button 
                size="small" 
                endIcon={<ArrowForwardIcon />}
                onClick={() => navigate('/tasks')}
              >
                Browse
              </Button>
            </CardActions>
          </Card>
        </Grid>
      </Grid>

      {/* Recent Tasks */}
      <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h5" gutterBottom>
          Recent Tasks
        </Typography>
        <Button 
          size="small" 
          endIcon={<ArrowForwardIcon />}
          onClick={() => navigate('/tasks')}
        >
          View All
        </Button>
      </Box>
      {loading ? (
        <LinearProgress sx={{ mb: 2 }} />
      ) : (
        <Grid container spacing={2}>
          {tasks.map((task) => (
            <Grid item xs={12} key={task.id}>
              <Paper
                elevation={0}
                sx={{
                  p: 2,
                  borderRadius: 2,
                  boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
                  border: '1px solid rgba(0,0,0,0.08)',
                  transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                  },
                }}
              >
                <Grid container alignItems="center" spacing={2}>
                  <Grid item>
                    <Tooltip title={task.task_type}>
                      <Box
                        sx={{
                          backgroundColor: task.task_type === 'infrastructure_generation' ? 'primary.light' : 'error.light',
                          borderRadius: '50%',
                          p: 1,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                        }}
                      >
                        {getTaskTypeIcon(task.task_type)}
                      </Box>
                    </Tooltip>
                  </Grid>
                  <Grid item xs>
                    <Typography variant="subtitle1">
                      {task.description || task.task_type.replace('_', ' ')}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {new Date(task.created_at).toLocaleString()}
                    </Typography>
                  </Grid>
                  <Grid item>
                    <Tooltip title={task.status}>
                      <Box>
                        {getStatusIcon(task.status)}
                      </Box>
                    </Tooltip>
                  </Grid>
                  <Grid item>
                    <IconButton
                      size="small"
                      onClick={() => navigate(`/tasks?id=${task.id}`)}
                    >
                      <ArrowForwardIcon fontSize="small" />
                    </IconButton>
                  </Grid>
                </Grid>
              </Paper>
            </Grid>
          ))}
          {tasks.length === 0 && (
            <Grid item xs={12}>
              <Paper
                elevation={0}
                sx={{
                  p: 3,
                  borderRadius: 2,
                  textAlign: 'center',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
                  border: '1px solid rgba(0,0,0,0.08)',
                }}
              >
                <Typography variant="body1" color="text.secondary">
                  No recent tasks found
                </Typography>
                <Button
                  variant="contained"
                  sx={{ mt: 2 }}
                  onClick={() => navigate('/generate')}
                >
                  Generate Infrastructure
                </Button>
              </Paper>
            </Grid>
          )}
        </Grid>
      )}
    </Box>
  );
}

export default Dashboard; 