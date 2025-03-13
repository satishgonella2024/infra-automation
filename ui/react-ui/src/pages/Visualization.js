import React, { useState, useEffect, useRef } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Grid, 
  FormControl, 
  InputLabel, 
  Select, 
  MenuItem, 
  Button,
  Card,
  CardContent,
  CircularProgress,
  Alert
} from '@mui/material';
import { Network } from 'vis-network';
import { fetchTasks, getInfrastructureVisualization } from '../services/api';

// Helper function to safely format task IDs
const formatTaskId = (id) => {
  if (!id) return 'N/A';
  return typeof id === 'string' && id.length > 8 ? `${id.substring(0, 8)}...` : id;
};

// Helper function to safely get task ID
const getTaskId = (task) => {
  return task && (task.id || task.task_id);
};

function Visualization() {
  const [tasks, setTasks] = useState([]);
  const [selectedTask, setSelectedTask] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [visualizationData, setVisualizationData] = useState(null);
  const networkContainer = useRef(null);
  const networkInstance = useRef(null);

  useEffect(() => {
    const loadTasks = async () => {
      try {
        setLoading(true);
        const response = await fetchTasks(20, 0, 'infrastructure_generation');
        setTasks(response);
      } catch (err) {
        console.error('Failed to fetch tasks:', err);
        setError('Failed to load tasks. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    loadTasks();
  }, []);

  useEffect(() => {
    if (visualizationData && networkContainer.current) {
      // Destroy previous network if it exists
      if (networkInstance.current) {
        networkInstance.current.destroy();
      }

      // Create a new network
      const options = {
        nodes: {
          shape: 'box',
          margin: 10,
          font: {
            size: 14
          },
          borderWidth: 2,
          shadow: true
        },
        edges: {
          width: 2,
          shadow: true,
          arrows: {
            to: { enabled: true, scaleFactor: 1 }
          }
        },
        physics: {
          stabilization: true,
          barnesHut: {
            gravitationalConstant: -5000,
            springConstant: 0.001,
            springLength: 200
          }
        },
        layout: {
          hierarchical: {
            enabled: true,
            direction: 'UD',
            sortMethod: 'directed',
            nodeSpacing: 150,
            levelSeparation: 150
          }
        }
      };

      networkInstance.current = new Network(
        networkContainer.current,
        visualizationData,
        options
      );

      // Add event listeners if needed
      networkInstance.current.on('click', function(params) {
        if (params.nodes.length > 0) {
          console.log('Clicked node:', params.nodes[0]);
          // You can add node details display here
        }
      });
    }
  }, [visualizationData]);

  const handleTaskChange = (event) => {
    setSelectedTask(event.target.value);
  };

  const handleVisualize = async () => {
    if (!selectedTask) return;

    try {
      setLoading(true);
      setError(null);
      const data = await getInfrastructureVisualization(selectedTask);
      
      // Check if we got valid visualization data
      if (!data || (!data.nodes && !data.edges)) {
        setError('No visualization data available for this task. Showing sample visualization instead.');
        createSampleVisualization();
      } else {
        // Check if this is the sample data (a simple way to detect is by checking the first node's label)
        const isSampleData = data.nodes && data.nodes[0] && data.nodes[0].label === 'VPC';
        
        if (isSampleData) {
          setError('The visualization API endpoint is not available. Showing sample visualization instead.');
        }
        
        setVisualizationData(data);
      }
    } catch (err) {
      console.error('Failed to fetch visualization:', err);
      
      // Set a more informative error message
      if (err.response && err.response.status === 404) {
        setError('The visualization API endpoint is not available. Showing sample visualization instead.');
      } else {
        setError('Failed to generate visualization. Showing sample visualization instead.');
      }
      
      // Automatically show sample data when there's an error
      createSampleVisualization();
    } finally {
      setLoading(false);
    }
  };

  // If API doesn't support visualization yet, create sample data
  const createSampleVisualization = () => {
    const sampleData = {
      nodes: [
        { id: 1, label: 'VPC', color: '#1976d2' },
        { id: 2, label: 'Public Subnet', color: '#4caf50' },
        { id: 3, label: 'Private Subnet', color: '#ff9800' },
        { id: 4, label: 'EC2 Instance', color: '#f44336' },
        { id: 5, label: 'RDS Database', color: '#9c27b0' },
        { id: 6, label: 'S3 Bucket', color: '#00bcd4' },
        { id: 7, label: 'Load Balancer', color: '#3f51b5' }
      ],
      edges: [
        { from: 1, to: 2 },
        { from: 1, to: 3 },
        { from: 2, to: 4 },
        { from: 2, to: 7 },
        { from: 3, to: 5 },
        { from: 7, to: 4 },
        { from: 4, to: 5 },
        { from: 4, to: 6 }
      ]
    };
    setVisualizationData(sampleData);
  };

  return (
    <Box className="slide-in-up">
      <Typography variant="h4" component="h1" gutterBottom>
        Infrastructure Visualization
      </Typography>
      <Typography variant="body1" paragraph>
        Visualize your infrastructure as an interactive network graph.
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Select Infrastructure
              </Typography>
              
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel id="task-select-label">Infrastructure Task</InputLabel>
                <Select
                  labelId="task-select-label"
                  id="task-select"
                  value={selectedTask}
                  label="Infrastructure Task"
                  onChange={handleTaskChange}
                  disabled={loading || tasks.length === 0}
                >
                  {tasks.map((task, index) => {
                    const taskId = getTaskId(task);
                    return (
                      <MenuItem key={taskId || index} value={taskId}>
                        {task.description || `Task ${formatTaskId(taskId)}`}
                      </MenuItem>
                    );
                  })}
                </Select>
              </FormControl>
              
              <Button
                variant="contained"
                color="primary"
                fullWidth
                onClick={handleVisualize}
                disabled={!selectedTask || loading}
                sx={{ mb: 2 }}
              >
                Visualize
              </Button>
              
              <Button
                variant="outlined"
                color="secondary"
                fullWidth
                onClick={createSampleVisualization}
                disabled={loading}
              >
                Show Sample
              </Button>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={8}>
          <Paper 
            sx={{ 
              p: 2, 
              height: '600px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              alignItems: 'center'
            }}
          >
            {loading ? (
              <Box sx={{ textAlign: 'center' }}>
                <CircularProgress />
                <Typography variant="body1" sx={{ mt: 2 }}>
                  Generating visualization...
                </Typography>
              </Box>
            ) : error ? (
              <Alert 
                severity="warning" 
                sx={{ width: '100%', mb: 2 }}
                action={
                  <Button 
                    color="inherit" 
                    size="small"
                    onClick={createSampleVisualization}
                  >
                    Show Sample
                  </Button>
                }
              >
                {error}
              </Alert>
            ) : !visualizationData ? (
              <Typography variant="body1" color="text.secondary">
                Select an infrastructure task and click "Visualize" to see the network graph,
                or click "Show Sample" to view an example.
              </Typography>
            ) : (
              <Box ref={networkContainer} sx={{ width: '100%', height: '100%' }} />
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}

export default Visualization; 