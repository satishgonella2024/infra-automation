// src/pages/WorkflowEditor.js
import React, { useState, useCallback, useEffect, useRef } from 'react';
import {
  Box,
  Typography,
  Paper,
  Drawer,
  Button,
  Alert,
  Snackbar,
  CircularProgress,
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Save as SaveIcon,
  Article as ArticleIcon,
  GitHub as GitHubIcon,
  Storage as StorageIcon,
  Code as CodeIcon,
  Security as SecurityIcon,
  Cloud as CloudIcon,
  Build as BuildIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { ReactFlowProvider } from 'reactflow';

// Import components
import WorkflowCanvas from '../components/WorkflowCanvas';
import AgentPanel from '../components/AgentPanel';

// Import API
import api from '../api';

const WorkflowEditor = () => {
  const editorRef = useRef(null);
  const [agents, setAgents] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [workflow, setWorkflow] = useState({ nodes: [], edges: [] });
  const [isRunning, setIsRunning] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(true);
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'info' });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Define available agent types with icons and colors
  const agentTypes = [
    {
      id: 'jira',
      name: 'Jira Agent',
      icon: <ArticleIcon />,
      color: '#0052CC',
      description: 'Manages Jira issues and workflows'
    },
    {
      id: 'confluence',
      name: 'Confluence Agent',
      icon: <ArticleIcon />,
      color: '#172B4D',
      description: 'Handles Confluence documentation'
    },
    {
      id: 'github',
      name: 'GitHub Agent',
      icon: <GitHubIcon />,
      color: '#24292E',
      description: 'Manages GitHub repositories and actions'
    },
    {
      id: 'nexus',
      name: 'Nexus Agent',
      icon: <StorageIcon />,
      color: '#1B75BB',
      description: 'Handles artifact management'
    },
    {
      id: 'kubernetes',
      name: 'Kubernetes Agent',
      icon: <CloudIcon />,
      color: '#326CE5',
      description: 'Manages Kubernetes resources'
    },
    {
      id: 'argocd',
      name: 'ArgoCD Agent',
      icon: <BuildIcon />,
      color: '#EF7B4D',
      description: 'Handles GitOps deployments'
    },
    {
      id: 'vault',
      name: 'Vault Agent',
      icon: <SecurityIcon />,
      color: '#000000',
      description: 'Manages secrets and security'
    },
    {
      id: 'security_scanner',
      name: 'Security Scanner',
      icon: <CodeIcon />,
      color: '#FF0000',
      description: 'Performs security scans'
    }
  ];

  // Helper functions for agent styling
  const getAgentColor = (type) => {
    const colors = {
      'jira': '#0052CC',
      'confluence': '#172B4D',
      'github': '#24292E',
      'nexus': '#1B75BB',
      'kubernetes': '#326CE5',
      'argocd': '#EF7B4D',
      'vault': '#000000',
      'security_scanner': '#FF0000',
      'default': '#666666'
    };
    return colors[type] || colors.default;
  };

  const getAgentIcon = (type) => {
    const icons = {
      'jira': <ArticleIcon />,
      'confluence': <ArticleIcon />,
      'github': <GitHubIcon />,
      'nexus': <StorageIcon />,
      'kubernetes': <CloudIcon />,
      'argocd': <BuildIcon />,
      'vault': <SecurityIcon />,
      'security_scanner': <CodeIcon />,
    };
    return icons[type] || <SettingsIcon />;
  };

  // Function to create sample agents (renamed to not use 'use' prefix which is reserved for hooks)
  const createSampleAgents = () => {
    // Use agentTypes as fallback data
    const sampleAgents = agentTypes.map((agent, index) => ({
      id: `${agent.id}-sample-${index}`,
      name: agent.name,
      type: agent.id,
      description: agent.description,
      status: 'idle',
      color: agent.color,
      icon: agent.icon,
      position: { x: 100 + (index * 50), y: 100 + (index * 30) }
    }));
    
    setAgents(sampleAgents);
    showNotification('Using sample agents. Backend connection failed.', 'warning');
  };

  // Show notification
  const showNotification = (message, severity = 'info') => {
    setNotification({
      open: true,
      message,
      severity,
    });
  };

  // Load agents from API with proper error handling
  useEffect(() => {
    const fetchAgents = async () => {
      setLoading(true);
      setError(null);
      
      try {
        // Use the helper function for consistent error handling and fallback
        const response = await api.getAgentStatus();
        console.log('API Response:', response);
        
        if (response.data && response.data.agents) {
          // Convert the agents object to an array with IDs
          const agentsArray = Object.entries(response.data.agents).map(([id, agent]) => ({
            ...agent,
            id,
            status: agent.state || 'idle',
            color: getAgentColor(id),
            icon: getAgentIcon(id),
          }));
          
          console.log('Processed agents:', agentsArray);
          setAgents(agentsArray);
        } else {
          console.warn('API response missing agents data, using fallback');
          // Fallback to sample agents
          createSampleAgents();
        }
      } catch (error) {
        console.warn('API fetch failed, using sample agents:', error);
        createSampleAgents();
      } finally {
        setLoading(false);
      }
    };
    
    fetchAgents();
  }, []);

  // Handle workflow changes
  const handleWorkflowChange = useCallback((newWorkflow) => {
    setWorkflow(newWorkflow);
  }, []);

  // Handle agent selection
  const handleAgentSelect = useCallback((agent) => {
    setSelectedAgent(agent);
    setDrawerOpen(true);
  }, []);

  // Save workflow with proper error handling
  const handleSave = async () => {
    try {
      // Validate workflow before saving
      if (!workflow.nodes || workflow.nodes.length === 0) {
        showNotification('Workflow is empty. Add some agents first.', 'warning');
        return;
      }
      
      try {
        const response = await api.post('/api/workflows', workflow);
        showNotification('Workflow saved successfully', 'success');
      } catch (apiError) {
        console.warn('API save failed, saving locally:', apiError);
        // Simulate successful save for demo purposes
        localStorage.setItem('savedWorkflow', JSON.stringify(workflow));
        showNotification('Workflow saved locally (API not available)', 'info');
      }
    } catch (error) {
      console.error('Failed to save workflow:', error);
      showNotification('Failed to save workflow: ' + (error.message || 'Unknown error'), 'error');
    }
  };

  // Start workflow execution with proper error handling
  const handleStart = async () => {
    try {
      // Validate workflow before execution
      if (!workflow.nodes || workflow.nodes.length === 0) {
        showNotification('Cannot run an empty workflow. Add some agents first.', 'warning');
        return;
      }
      
      if (!workflow.edges || workflow.edges.length === 0) {
        showNotification('Workflow has no connections. Connect your agents first.', 'warning');
        return;
      }
      
      try {
        await api.post('/api/workflows/execute', workflow);
        setIsRunning(true);
        showNotification('Workflow execution started', 'success');
      } catch (apiError) {
        console.warn('API execution failed, simulating locally:', apiError);
        // Simulate execution for demo purposes
        setIsRunning(true);
        showNotification('Workflow execution simulated (API not available)', 'info');
      }
      
      // Update agent status
      const updatedAgents = agents.map(agent => {
        const workflowNode = workflow.nodes.find(node => node.id === agent.id);
        return workflowNode ? { ...agent, status: 'active' } : agent;
      });
      setAgents(updatedAgents);
      
      // Simulate completion after 5 seconds for demo purposes
      setTimeout(() => {
        handleStop();
      }, 5000);
    } catch (error) {
      console.error('Failed to start workflow:', error);
      showNotification('Failed to start workflow: ' + (error.message || 'Unknown error'), 'error');
    }
  };

  // Stop workflow execution with proper error handling
  const handleStop = async () => {
    try {
      try {
        await api.post('/api/workflows/stop');
      } catch (apiError) {
        console.warn('API stop failed, stopping locally:', apiError);
        // No action needed, we'll update UI state anyway
      }
      
      setIsRunning(false);
      showNotification('Workflow execution stopped', 'info');
      
      const updatedAgents = agents.map(agent => ({
        ...agent,
        status: 'idle'
      }));
      setAgents(updatedAgents);
    } catch (error) {
      console.error('Failed to stop workflow:', error);
      showNotification('Failed to stop workflow: ' + (error.message || 'Unknown error'), 'error');
    }
  };

  // Close notification
  const handleCloseNotification = () => {
    setNotification(prev => ({ ...prev, open: false }));
  };

  // Render loading state
  if (loading) {
    return (
      <Box 
        sx={{ 
          display: 'flex', 
          flexDirection: 'column',
          alignItems: 'center', 
          justifyContent: 'center', 
          height: '100vh' 
        }}
      >
        <CircularProgress size={60} sx={{ mb: 3 }} />
        <Typography variant="h6">Loading Workflow Editor...</Typography>
      </Box>
    );
  }

  // Render error state
  if (error) {
    return (
      <Box 
        sx={{ 
          display: 'flex', 
          flexDirection: 'column',
          alignItems: 'center', 
          justifyContent: 'center', 
          height: '100vh',
          p: 3
        }}
      >
        <Alert severity="error" sx={{ mb: 3, width: '100%', maxWidth: 600 }}>
          {error}
        </Alert>
        <Button 
          variant="contained" 
          onClick={() => window.location.reload()}
        >
          Retry
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'flex', height: '100vh', bgcolor: '#f5f5f5' }}>
      {/* Agent Library Sidebar */}
      <Paper
        elevation={2}
        sx={{
          width: 280,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          bgcolor: 'background.paper',
        }}
      >
        <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
          <Typography variant="h6" fontWeight="bold">Agent Library</Typography>
        </Box>

        <Box sx={{ p: 2, overflowY: 'auto', flex: 1 }}>
          {agentTypes.map((agent) => (
            <Paper
              key={agent.id}
              elevation={0}
              sx={{
                p: 2,
                mb: 1,
                cursor: 'grab',
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                bgcolor: 'grey.50',
                '&:hover': {
                  bgcolor: 'grey.100',
                },
                borderLeft: 3,
                borderColor: agent.color,
              }}
              draggable
              onDragStart={(e) => {
                e.dataTransfer.setData(
                  'application/json',
                  JSON.stringify(agent)
                );
              }}
            >
              <Box sx={{ color: agent.color }}>{agent.icon}</Box>
              <Box>
                <Typography variant="subtitle2">{agent.name}</Typography>
                <Typography variant="caption" color="text.secondary">
                  {agent.description}
                </Typography>
              </Box>
            </Paper>
          ))}
        </Box>

        <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
          <Button
            fullWidth
            variant="contained"
            color="primary"
            startIcon={isRunning ? <StopIcon /> : <PlayIcon />}
            onClick={isRunning ? handleStop : handleStart}
          >
            {isRunning ? 'Stop Workflow' : 'Run Workflow'}
          </Button>
          <Button
            fullWidth
            variant="outlined"
            startIcon={<SaveIcon />}
            onClick={handleSave}
            sx={{ mt: 1 }}
          >
            Save Workflow
          </Button>
        </Box>
      </Paper>

      {/* Main Canvas */}
      <Box sx={{ flex: 1, position: 'relative' }} ref={editorRef}>
        <ReactFlowProvider>
          <WorkflowCanvas
            agents={agents}
            onAgentSelect={handleAgentSelect}
            onWorkflowChange={handleWorkflowChange}
          />
        </ReactFlowProvider>
      </Box>

      {/* Configuration Panel */}
      <Drawer
        anchor="right"
        open={drawerOpen && selectedAgent !== null}
        onClose={() => setDrawerOpen(false)}
        PaperProps={{
          sx: { width: 320 }
        }}
      >
        {selectedAgent && (
          <AgentPanel
            agent={selectedAgent}
            onUpdate={(updatedAgent) => {
              const updatedAgents = agents.map(a =>
                a.id === updatedAgent.id ? { ...a, ...updatedAgent } : a
              );
              setAgents(updatedAgents);
            }}
          />
        )}
      </Drawer>

      {/* Notifications */}
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={handleCloseNotification}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={handleCloseNotification}
          severity={notification.severity}
          variant="filled"
          sx={{ width: '100%' }}
        >
          {notification.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default WorkflowEditor;