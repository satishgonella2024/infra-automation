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
  Tooltip,
  CircularProgress
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
  Warning as WarningIcon,
  Memory,
  Storage,
  Speed,
  Memory as GpuIcon
} from '@mui/icons-material';
import { fetchTasks } from '../services/api';
import { Chart as ChartJS, ArcElement, Tooltip as ChartTooltip, Legend } from 'chart.js';
import { Doughnut } from 'react-chartjs-2';
import LoadingIndicator from '../components/LoadingIndicator';
import AgentStatus from '../components/AgentStatus';
import { formatDistanceToNow } from 'date-fns';

// Register Chart.js components
ChartJS.register(ArcElement, ChartTooltip, Legend);

// Helper function to format task type
const formatTaskType = (type) => {
  if (!type) return 'Unknown Task';
  return type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
};

// Helper function to safely get task ID
const getTaskId = (task) => {
  return task && (task.id || task.task_id);
};

const MetricCard = ({ title, value, icon, tooltip }) => (
  <Tooltip title={tooltip}>
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box display="flex" alignItems="center" mb={2}>
          {icon}
          <Typography variant="h6" component="div" ml={1}>
            {title}
          </Typography>
        </Box>
        <Typography variant="h4" component="div">
          {value}
        </Typography>
      </CardContent>
    </Card>
  </Tooltip>
);

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
  const [metrics, setMetrics] = useState(null);
  const [error, setError] = useState(null);

  // Load tasks on component mount
  useEffect(() => {
    loadTasks();
    // Set up polling to refresh tasks every 30 seconds
    const interval = setInterval(loadTasks, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await fetch('http://localhost:8000/metrics');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setMetrics(data);
        setError(null);
      } catch (e) {
        setError(e.message);
      }
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 5000); // Update every 5 seconds
    return () => clearInterval(interval);
  }, []);

  // Load tasks from API
  const loadTasks = async () => {
    try {
      setLoading(true);
      const response = await fetchTasks(5);
      
      // Ensure we have an array of tasks
      const taskList = Array.isArray(response) ? response : [];
      setTasks(taskList);
      
      // Calculate statistics
      const total = taskList.length;
      const successful = taskList.filter(task => task.status === 'completed' || task.status === 'success').length;
      const failed = taskList.filter(task => task.status === 'failed' || task.status === 'error').length;
      const inProgress = taskList.filter(task => task.status === 'processing' || task.status === 'in_progress').length;
      
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

  // Handle refresh button click
  const handleRefresh = async () => {
    await loadTasks();
  };

  // Helper function to get status icon
  const getStatusIcon = (status) => {
    if (!status) return <WarningIcon color="warning" />;
    
    status = String(status || '').toLowerCase();
    switch (status) {
      case 'completed':
      case 'success':
        return <CheckCircleIcon color="success" />;
      case 'failed':
      case 'error':
        return <ErrorIcon color="error" />;
      case 'processing':
      case 'in_progress':
        return <WarningIcon color="warning" />;
      default:
        return <HistoryIcon />;
    }
  };

  // Helper function to get task type icon
  const getTaskTypeIcon = (type) => {
    if (!type) return <CodeIcon />;
    
    type = String(type || '').toLowerCase();
    switch (type) {
      case 'infrastructure_generation':
        return <CodeIcon />;
      case 'security_review':
        return <SecurityIcon />;
      default:
        return <HistoryIcon />;
    }
  };

  // Helper function to determine agent status color
  const getAgentStatusColor = (status) => {
    if (!status) return 'default';
    
    status = String(status || '').toLowerCase();
    if (status === 'idle' || status === 'online' || status === 'running') return 'success';
    if (status === 'processing' || status === 'busy') return 'warning';
    if (status === 'error' || status === 'offline') return 'error';
    return 'default';
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

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box p={3}>
        <Typography color="error">Error loading metrics: {error}</Typography>
      </Box>
    );
  }

  const formatBytes = (bytes) => {
    return `${Math.round(bytes * 10) / 10} GB`;
  };

  const formatPercent = (value) => {
    return `${Math.round(value)}%`;
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

      {apiStatus && apiStatus.agents && <AgentStatus agents={apiStatus.agents} />}

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
                label={apiStatus?.status || 'unknown'}
                color={apiStatus?.status === 'online' ? 'success' : 'error'}
                sx={{ mr: 1 }}
              />
              <Typography variant="body2" color="text.secondary">
                {apiStatus?.status === 'online' ? 'System is operational' : 'System is offline'}
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
              System Information
            </Typography>
            <Typography variant="body1">
              Version: {apiStatus.version}
            </Typography>
            <Typography variant="body1">
              Uptime: {Math.floor(apiStatus.uptime_seconds / 3600)} hours {Math.floor((apiStatus.uptime_seconds % 3600) / 60)} minutes
            </Typography>
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
                    backgroundColor: 'success.light',
                    borderRadius: '50%',
                    p: 1,
                    mr: 2,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <Storage sx={{ color: 'success.main' }} />
                </Box>
                <Typography variant="h6">
                  Terraform Modules
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Create enterprise-grade Terraform modules with best practices
              </Typography>
            </CardContent>
            <CardActions>
              <Button 
                size="small" 
                endIcon={<ArrowForwardIcon />}
                onClick={() => navigate('/terraform-modules')}
              >
                Create
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
        <Box sx={{ my: 4, display: 'flex', justifyContent: 'center' }}>
          <LoadingIndicator 
            message="Loading recent tasks..." 
            showProgress={false}
            timeout={30} // 30 seconds timeout
          />
        </Box>
      ) : (
        <Grid container spacing={2}>
          {tasks.map((task, index) => (
            <Grid item xs={12} key={getTaskId(task) || index}>
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
                    <Tooltip title={task.task_type || 'Unknown Task Type'}>
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
                      {task.description || formatTaskType(task.task_type)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {task.created_at ? new Date(task.created_at).toLocaleString() : 
                       task.timestamp ? new Date(task.timestamp).toLocaleString() : 'Unknown date'}
                    </Typography>
                  </Grid>
                  <Grid item>
                    <Tooltip title={task.status || 'Unknown Status'}>
                      <Box>
                        {getStatusIcon(task.status)}
                      </Box>
                    </Tooltip>
                  </Grid>
                  <Grid item>
                    <IconButton
                      size="small"
                      onClick={() => {
                        const taskId = getTaskId(task);
                        if (taskId) {
                          navigate(`/tasks?id=${taskId}`);
                        } else {
                          navigate('/tasks');
                        }
                      }}
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

      {/* System Metrics */}
      <Typography variant="h5" gutterBottom sx={{ mb: 2 }}>
        System Metrics
      </Typography>
      <Grid container spacing={3} mb={3}>
        {metrics && metrics.gpu_usage !== null && (
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="GPU Usage"
              value="N/A"
              icon={<GpuIcon color="primary" />}
              tooltip="GPU metrics not available"
            />
          </Grid>
        )}
        
        {metrics && (
          <>
            <Grid item xs={12} sm={6} md={3}>
              <MetricCard
                title="CPU Usage"
                value={metrics.cpu_usage !== undefined ? formatPercent(metrics.cpu_usage) : 'N/A'}
                icon={<Speed color="primary" />}
                tooltip="Current CPU utilization"
              />
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <MetricCard
                title="Memory Usage"
                value={metrics.memory_usage?.percent !== undefined ? 
                  formatPercent(metrics.memory_usage.percent) : 'N/A'}
                icon={<Memory color="primary" />}
                tooltip={metrics.memory_usage?.used_gb !== undefined ? 
                  `${formatBytes(metrics.memory_usage.used_gb)} / ${formatBytes(metrics.memory_usage.total_gb)}` :
                  'Memory metrics not available'
                }
              />
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <MetricCard
                title="Disk Usage"
                value={metrics.disk_usage?.percent !== undefined ? 
                  formatPercent(metrics.disk_usage.percent) : 'N/A'}
                icon={<Storage color="primary" />}
                tooltip={metrics.disk_usage?.used ? 
                  `${metrics.disk_usage.used} / ${metrics.disk_usage.total}` :
                  'Disk metrics not available'
                }
              />
            </Grid>
          </>
        )}
      </Grid>

      {/* LLM Service Metrics */}
      {metrics && metrics.llm_metrics && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              LLM Service Metrics
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={4}>
                <Typography variant="body1">
                  Total Requests: {metrics.llm_metrics.total_requests || 0}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Typography variant="body1">
                  Active Requests: {metrics.llm_metrics.active_requests || 0}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Typography variant="body1">
                  Last Request: {metrics.llm_metrics.last_request_time ? 
                    formatDistanceToNow(new Date(metrics.llm_metrics.last_request_time), { addSuffix: true }) :
                    'Never'}
                </Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {metrics && metrics.agents && <AgentStatus agents={metrics.agents} />}
    </Box>
  );
}

export default Dashboard; 