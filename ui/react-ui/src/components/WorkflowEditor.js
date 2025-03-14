// src/components/WorkflowEditor.js
import React, { useState, useEffect, useCallback } from 'react';
import ReactFlow, { 
  Controls, 
  Background, 
  MiniMap, 
  addEdge, 
  removeElements, 
  isNode,
  isEdge
} from 'react-flow-renderer';
import {
  Box,
  Button,
  Card,
  CardContent,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  FormControl,
  Grid,
  IconButton,
  InputLabel,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  MenuItem,
  Paper,
  Select,
  Tab,
  Tabs,
  TextField,
  Typography,
  Drawer,
  Chip
} from '@mui/material';
import {
  Add as AddIcon,
  Close as CloseIcon,
  Delete as DeleteIcon,
  Save as SaveIcon,
  PlayArrow as RunIcon,
  Edit as EditIcon,
  Code as CodeIcon,
  Settings as SettingsIcon,
  DragIndicator as DragIcon,
  ExpandMore as ExpandMoreIcon,
  ChevronRight as ChevronRightIcon
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import api from '../api';

// Node types
const nodeTypes = {
  agent: AgentNode
};

// Styled component for the agent sidebar
const StyledAgentList = styled(List)(({ theme }) => ({
  width: '100%',
  maxWidth: 360,
  backgroundColor: theme.palette.background.paper,
  '& .MuiListItemIcon-root': {
    minWidth: 36
  }
}));

// Styled component for the workflow node
const WorkflowNodeWrapper = styled(Box)(({ theme, selected }) => ({
  display: 'flex',
  flexDirection: 'column',
  padding: theme.spacing(1),
  borderRadius: theme.shape.borderRadius,
  backgroundColor: selected ? theme.palette.primary.light : theme.palette.background.paper,
  border: `1px solid ${selected ? theme.palette.primary.main : theme.palette.divider}`,
  boxShadow: theme.shadows[2],
  minWidth: 200,
  '&:hover': {
    boxShadow: theme.shadows[3],
    cursor: 'pointer'
  }
}));

// Custom node component for agents
function AgentNode({ data, selected }) {
  return (
    <WorkflowNodeWrapper selected={selected}>
      <Box display="flex" justifyContent="space-between" alignItems="center">
        <Typography variant="subtitle1" color="textPrimary">
          {data.label}
        </Typography>
        <Chip 
          label={data.agent}
          size="small"
          style={{ 
            backgroundColor: data.agentColor || '#e0e0e0',
            color: '#fff'
          }}
        />
      </Box>
      
      <Divider style={{ margin: '8px 0' }} />
      
      <Typography variant="body2" color="textSecondary">
        {data.action}
      </Typography>
      
      {data.description && (
        <Typography variant="caption" color="textSecondary" style={{ marginTop: 4 }}>
          {data.description}
        </Typography>
      )}
      
      {data.status && (
        <Chip 
          label={data.status}
          size="small"
          style={{ marginTop: 8, alignSelf: 'flex-start' }}
          color={
            data.status === 'succeeded' ? 'success' :
            data.status === 'failed' ? 'error' :
            data.status === 'running' ? 'info' :
            'default'
          }
        />
      )}
    </WorkflowNodeWrapper>
  );
}

// Agent colors
const AGENT_COLORS = {
  'infrastructure': '#1976d2',
  'architecture': '#388e3c',
  'security': '#d32f2f',
  'cost': '#f57c00',
  'jira': '#0052cc',
  'github': '#24292e',
  'confluence': '#0052cc',
  'kubernetes': '#326ce5',
  'argocd': '#326ce5',
  'vault': '#000000',
  'security_scanner': '#d32f2f'
};

function WorkflowEditor() {
  const [agents, setAgents] = useState({});
  const [templates, setTemplates] = useState([]);
  const [workflowDefinitions, setWorkflowDefinitions] = useState([]);
  const [selectedDefinition, setSelectedDefinition] = useState(null);
  const [elements, setElements] = useState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const [nodeName, setNodeName] = useState('');
  const [nodeAgent, setNodeAgent] = useState('');
  const [nodeAction, setNodeAction] = useState('');
  const [nodeDescription, setNodeDescription] = useState('');
  const [nodeParameters, setNodeParameters] = useState({});
  const [nodeDependsOn, setNodeDependsOn] = useState([]);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [isNewWorkflowDialogOpen, setIsNewWorkflowDialogOpen] = useState(false);
  const [newWorkflowName, setNewWorkflowName] = useState('');
  const [newWorkflowDescription, setNewWorkflowDescription] = useState('');
  const [isTemplateDialogOpen, setIsTemplateDialogOpen] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [drawerOpen, setDrawerOpen] = useState(true);
  const [sidebarTab, setSidebarTab] = useState(0);
  const [workflowMetadata, setWorkflowMetadata] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [jsonView, setJsonView] = useState(false);
  const [workflowJson, setWorkflowJson] = useState('');
  
  // Fetch agents and workflow definitions on component mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Fetch agents
        const agentsResponse = await api.get('/api/workflows/agents');
        setAgents(agentsResponse.data);
        
        // Fetch workflow definitions
        const definitionsResponse = await api.get('/api/workflows');
        setWorkflowDefinitions(definitionsResponse.data);
        
        // Fetch template types
        const templatesResponse = await api.get('/api/workflows/templates');
        setTemplates(templatesResponse.data);
        
        setLoading(false);
      } catch (error) {
        setError('Error loading data. Please try again.');
        setLoading(false);
        console.error('Error fetching workflow data:', error);
      }
    };
    
    fetchData();
  }, []);
  
  // Update elements when selected definition changes
  useEffect(() => {
    if (selectedDefinition) {
      convertDefinitionToElements(selectedDefinition);
      setWorkflowMetadata(selectedDefinition.metadata || {});
      updateWorkflowJson(selectedDefinition);
    } else {
      setElements([]);
      setWorkflowMetadata({});
      setWorkflowJson('');
    }
  }, [selectedDefinition]);
  
  // Convert workflow definition to ReactFlow elements
  const convertDefinitionToElements = (definition) => {
    if (!definition || !definition.steps) return;
    
    const nodes = definition.steps.map((step, index) => {
      // Calculate position
      const position = calculateNodePosition(step, index, definition.steps.length);
      
      return {
        id: step.id,
        type: 'agent',
        position,
        data: {
          label: step.name,
          agent: step.agent,
          action: step.action,
          description: step.description,
          agentColor: AGENT_COLORS[step.agent] || '#757575',
          parameters: step.parameters,
          depends_on: step.depends_on || [],
          condition: step.condition
        }
      };
    });
    
    const edges = [];
    definition.steps.forEach(step => {
      if (step.depends_on && step.depends_on.length > 0) {
        step.depends_on.forEach(sourceId => {
          edges.push({
            id: `${sourceId}-${step.id}`,
            source: sourceId,
            target: step.id,
            animated: true,
            style: { stroke: '#999' }
          });
        });
      }
    });
    
    setElements([...nodes, ...edges]);
  };
  
  // Calculate node position based on dependencies
  const calculateNodePosition = (step, index, totalSteps) => {
    // Simple layout: steps in a grid
    const column = Math.min(index % 3, 2);
    const row = Math.floor(index / 3);
    
    return {
      x: 250 * column + 50,
      y: 150 * row + 50
    };
  };
  
  // Update JSON view
  const updateWorkflowJson = (definition) => {
    if (!definition) {
      setWorkflowJson('');
      return;
    }
    
    try {
      const json = JSON.stringify(definition, null, 2);
      setWorkflowJson(json);
    } catch (error) {
      console.error('Error converting workflow to JSON:', error);
      setWorkflowJson('Error generating JSON');
    }
  };
  
  // Handle flow element click
  const onElementClick = (event, element) => {
    if (isNode(element)) {
      setSelectedNode(element);
      setNodeName(element.data.label);
      setNodeAgent(element.data.agent);
      setNodeAction(element.data.action);
      setNodeDescription(element.data.description || '');
      setNodeParameters(element.data.parameters || {});
      setNodeDependsOn(element.data.depends_on || []);
    } else {
      setSelectedNode(null);
    }
  };
  
  // Handle element removal
  const onElementsRemove = (elementsToRemove) => {
    setElements(els => removeElements(elementsToRemove, els));
    
    // If selected node is removed, clear selection
    if (elementsToRemove.some(el => el.id === selectedNode?.id)) {
      setSelectedNode(null);
    }
    
    // TODO: Update workflow definition
  };
  
  // Handle connection creation
  const onConnect = (params) => {
    // Add the edge
    setElements(els => addEdge({
      ...params,
      animated: true,
      style: { stroke: '#999' }
    }, els));
    
    // Update node dependencies
    const targetNode = elements.find(el => el.id === params.target);
    if (targetNode) {
      const depends_on = targetNode.data.depends_on || [];
      targetNode.data.depends_on = [...depends_on, params.source];
      
      // TODO: Update workflow definition
    }
  };
  
  // Open node edit dialog
  const handleEditNode = () => {
    if (selectedNode) {
      setIsEditDialogOpen(true);
    }
  };
  
  // Save node changes
  const handleSaveNode = () => {
    // Update the node
    setElements(els => {
      return els.map(el => {
        if (el.id === selectedNode.id) {
          // Update node data
          return {
            ...el,
            data: {
              ...el.data,
              label: nodeName,
              agent: nodeAgent,
              action: nodeAction,
              description: nodeDescription,
              parameters: nodeParameters,
              depends_on: nodeDependsOn
            }
          };
        }
        return el;
      });
    });
    
    // Close the dialog
    setIsEditDialogOpen(false);
    
    // TODO: Update workflow definition
  };
  
  // Delete selected node
  const handleDeleteNode = () => {
    if (selectedNode) {
      // Remove the node and its connections
      const nodesToRemove = [selectedNode];
      const edgesToRemove = elements.filter(el => 
        isEdge(el) && (el.source === selectedNode.id || el.target === selectedNode.id)
      );
      
      onElementsRemove([...nodesToRemove, ...edgesToRemove]);
    }
  };
  
  // Add new node
  const handleAddNode = (agent, action) => {
    // Create a new node ID
    const newNodeId = `node-${Date.now()}`;
    
    // Get agent color
    const agentColor = AGENT_COLORS[agent] || '#757575';
    
    // Get action details
    const agentActions = agents[agent]?.actions || {};
    const actionDetails = agentActions[action] || { name: action };
    
    // Calculate position (based on selected node or default)
    const position = selectedNode ? 
      { x: selectedNode.position.x + 250, y: selectedNode.position.y } :
      { x: 100, y: 100 };
    
    // Create new node
    const newNode = {
      id: newNodeId,
      type: 'agent',
      position,
      data: {
        label: `${actionDetails.name || action}`,
        agent,
        action,
        description: actionDetails.description || '',
        agentColor,
        parameters: {},
        depends_on: []
      }
    };
    
    // Add the node
    setElements(els => [...els, newNode]);
    
    // Select the new node
    setSelectedNode(newNode);
    setNodeName(newNode.data.label);
    setNodeAgent(newNode.data.agent);
    setNodeAction(newNode.data.action);
    setNodeDescription(newNode.data.description);
    setNodeParameters(newNode.data.parameters);
    setNodeDependsOn(newNode.data.depends_on);
    
    // Open edit dialog
    setIsEditDialogOpen(true);
    
    // TODO: Update workflow definition
  };
  
  // Open new workflow dialog
  const handleNewWorkflow = () => {
    setIsNewWorkflowDialogOpen(true);
  };
  
  // Create new workflow
  const handleCreateWorkflow = async () => {
    try {
      // Create a new workflow with a single node
      const newWorkflow = {
        name: newWorkflowName,
        description: newWorkflowDescription,
        steps: []
      };
      
      // Create the workflow definition
      const response = await api.post('/api/workflows', newWorkflow);
      
      // Add to workflow definitions
      setWorkflowDefinitions([...workflowDefinitions, response.data]);
      
      // Select the new workflow
      setSelectedDefinition(response.data);
      
      // Reset form
      setNewWorkflowName('');
      setNewWorkflowDescription('');
      
      // Close dialog
      setIsNewWorkflowDialogOpen(false);
    } catch (error) {
      console.error('Error creating workflow:', error);
      setError('Error creating workflow. Please try again.');
    }
  };
  
  // Open template dialog
  const handleCreateFromTemplate = () => {
    setIsTemplateDialogOpen(true);
  };
  
  // Create workflow from template
  const handleCreateFromTemplateConfirm = async () => {
    try {
      // Create workflow from template
      const response = await api.post('/api/workflows/templates', {
        template_type: selectedTemplate,
        name: newWorkflowName || `New ${selectedTemplate} Workflow`,
        description: newWorkflowDescription || `Workflow created from ${selectedTemplate} template`
      });
      
      // Add to workflow definitions
      setWorkflowDefinitions([...workflowDefinitions, response.data]);
      
      // Select the new workflow
      setSelectedDefinition(response.data);
      
      // Reset form
      setSelectedTemplate('');
      setNewWorkflowName('');
      setNewWorkflowDescription('');
      
      // Close dialog
      setIsTemplateDialogOpen(false);
    } catch (error) {
      console.error('Error creating workflow from template:', error);
      setError('Error creating workflow from template. Please try again.');
    }
  };
  
  // Save workflow changes
  const handleSaveWorkflow = async () => {
    if (!selectedDefinition) return;
    
    try {
      // Convert elements to workflow steps
      const nodes = elements.filter(el => isNode(el));
      const edges = elements.filter(el => isEdge(el));
      
      const steps = nodes.map(node => {
        // Find all edges where this node is the target
        const incomingEdges = edges.filter(edge => edge.target === node.id);
        
        // Extract source nodes as dependencies
        const depends_on = incomingEdges.map(edge => edge.source);
        
        return {
          id: node.id,
          name: node.data.label,
          description: node.data.description,
          agent: node.data.agent,
          action: node.data.action,
          parameters: node.data.parameters || {},
          depends_on: depends_on,
          condition: node.data.condition
        };
      });
      
      // Update workflow definition
      const updatedDefinition = {
        ...selectedDefinition,
        steps: steps,
        metadata: workflowMetadata
      };
      
      // Save to API
      const response = await api.put(`/api/workflows/${selectedDefinition.id}`, {
        name: selectedDefinition.name,
        description: selectedDefinition.description,
        steps: steps,
        metadata: workflowMetadata
      });
      
      // Update definitions list
      setWorkflowDefinitions(workflowDefinitions.map(def => 
        def.id === selectedDefinition.id ? response.data : def
      ));
      
      // Update selected definition
      setSelectedDefinition(response.data);
      
      // Show success message
      alert('Workflow saved successfully');
    } catch (error) {
      console.error('Error saving workflow:', error);
      setError('Error saving workflow. Please try again.');
    }
  };
  
  // Run workflow
  const handleRunWorkflow = async () => {
    if (!selectedDefinition) return;
    
    try {
      // Create workflow instance
      const response = await api.post('/api/workflows/instances', {
        definition_id: selectedDefinition.id,
        input_data: {}
      });
      
      // Show success message
      alert(`Workflow instance created with ID: ${response.data.id}`);
      
      // Redirect to instances page
      // history.push(`/workflow/instances/${response.data.id}`);
    } catch (error) {
      console.error('Error running workflow:', error);
      setError('Error running workflow. Please try again.');
    }
  };
  
  // Delete workflow
  const handleDeleteWorkflow = async () => {
    if (!selectedDefinition) return;
    
    if (window.confirm(`Are you sure you want to delete workflow "${selectedDefinition.name}"?`)) {
      try {
        // Delete from API
        await api.delete(`/api/workflows/${selectedDefinition.id}`);
        
        // Remove from definitions list
        setWorkflowDefinitions(workflowDefinitions.filter(def => def.id !== selectedDefinition.id));
        
        // Clear selected definition
        setSelectedDefinition(null);
        
        // Show success message
        alert('Workflow deleted successfully');
      } catch (error) {
        console.error('Error deleting workflow:', error);
        setError('Error deleting workflow. Please try again.');
      }
    }
  };
  
  // Copy workflow (duplicate)
  const handleCopyWorkflow = async () => {
    if (!selectedDefinition) return;
    
    try {
      // Create a new workflow with the same steps
      const newWorkflow = {
        name: `${selectedDefinition.name} (Copy)`,
        description: selectedDefinition.description,
        steps: selectedDefinition.steps,
        metadata: selectedDefinition.metadata
      };
      
      // Create the workflow definition
      const response = await api.post('/api/workflows', newWorkflow);
      
      // Add to workflow definitions
      setWorkflowDefinitions([...workflowDefinitions, response.data]);
      
      // Select the new workflow
      setSelectedDefinition(response.data);
      
      // Show success message
      alert('Workflow copied successfully');
    } catch (error) {
      console.error('Error copying workflow:', error);
      setError('Error copying workflow. Please try again.');
    }
  };
  
  // Toggle JSON view
  const handleToggleJsonView = () => {
    setJsonView(!jsonView);
  };
  
  // Update workflow from JSON
  const handleUpdateFromJson = () => {
    try {
      // Parse JSON
      const parsedJson = JSON.parse(workflowJson);
      
      // Validate
      if (!parsedJson.name || !parsedJson.steps) {
        throw new Error('Invalid workflow JSON');
      }
      
      // Update selected definition
      setSelectedDefinition(parsedJson);
      
      // Show success message
      alert('Workflow updated from JSON');
    } catch (error) {
      console.error('Error parsing workflow JSON:', error);
      setError('Error parsing workflow JSON. Please check the format.');
    }
  };
  
  // Render the component
  return (
    <Box sx={{ height: '100%', display: 'flex' }}>
      {/* Sidebar drawer */}
      <Drawer
        variant="persistent"
        anchor="left"
        open={drawerOpen}
        sx={{
          width: 300,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: 300,
            boxSizing: 'border-box',
            position: 'relative',
            height: '100%'
          }
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', p: 2, borderBottom: '1px solid rgba(0, 0, 0, 0.12)' }}>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Workflow Editor
          </Typography>
          <IconButton onClick={() => setDrawerOpen(false)} size="small">
            <ChevronRightIcon />
          </IconButton>
        </Box>
        
        <Box sx={{ p: 2 }}>
          <Tabs
            value={sidebarTab}
            onChange={(e, newValue) => setSidebarTab(newValue)}
            aria-label="sidebar tabs"
            variant="fullWidth"
          >
            <Tab label="Workflows" />
            <Tab label="Agents" />
          </Tabs>
          
          {sidebarTab === 0 && (
            <Box sx={{ mt: 2 }}>
              <Box sx={{ mb: 2, display: 'flex', gap: 1 }}>
                <Button
                  variant="outlined"
                  color="primary"
                  startIcon={<AddIcon />}
                  onClick={handleNewWorkflow}
                  size="small"
                  fullWidth
                >
                  New Workflow
                </Button>
                <Button
                  variant="outlined"
                  color="secondary"
                  startIcon={<AddIcon />}
                  onClick={handleCreateFromTemplate}
                  size="small"
                  fullWidth
                >
                  From Template
                </Button>
              </Box>
              
              <List
                sx={{
                  width: '100%',
                  maxHeight: 'calc(100vh - 300px)',
                  overflow: 'auto',
                  bgcolor: 'background.paper',
                  border: '1px solid rgba(0, 0, 0, 0.12)',
                  borderRadius: 1
                }}
              >
                {workflowDefinitions.map((workflow) => (
                  <ListItem
                    key={workflow.id}
                    button
                    selected={selectedDefinition?.id === workflow.id}
                    onClick={() => setSelectedDefinition(workflow)}
                  >
                    <ListItemText
                      primary={workflow.name}
                      secondary={workflow.description}
                    />
                  </ListItem>
                ))}
                {workflowDefinitions.length === 0 && (
                  <ListItem>
                    <ListItemText
                      primary="No workflows found"
                      secondary="Create a new workflow to get started"
                    />
                  </ListItem>
                )}
              </List>
              
              {selectedDefinition && (
                <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                  <Button
                    variant="contained"
                    color="primary"
                    startIcon={<SaveIcon />}
                    onClick={handleSaveWorkflow}
                    size="small"
                  >
                    Save
                  </Button>
                  <Button
                    variant="contained"
                    color="success"
                    startIcon={<RunIcon />}
                    onClick={handleRunWorkflow}
                    size="small"
                  >
                    Run
                  </Button>
                  <Button
                    variant="outlined"
                    color="error"
                    startIcon={<DeleteIcon />}
                    onClick={handleDeleteWorkflow}
                    size="small"
                  >
                    Delete
                  </Button>
                </Box>
              )}
            </Box>
          )}
          
          {sidebarTab === 1 && (
            <Box sx={{ mt: 2 }}>
              {Object.keys(agents).map((agentId) => {
                const agent = agents[agentId];
                const agentColor = AGENT_COLORS[agentId] || '#757575';
                
                return (
                  <Card key={agentId} sx={{ mb: 2 }}>
                    <CardContent sx={{ pb: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                        <Box
                          sx={{
                            width: 16,
                            height: 16,
                            borderRadius: '50%',
                            backgroundColor: agentColor,
                            mr: 1
                          }}
                        />
                        <Typography variant="subtitle1">
                          {agent.name}
                        </Typography>
                      </Box>
                      
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        {agent.description}
                      </Typography>
                      
                      <Divider sx={{ my: 1 }} />
                      
                      <Typography variant="subtitle2" sx={{ mb: 1 }}>
                        Actions:
                      </Typography>
                      
                      {Object.keys(agent.actions || {}).map((actionId) => {
                        const action = agent.actions[actionId];
                        return (
                          <Button
                            key={actionId}
                            variant="outlined"
                            size="small"
                            onClick={() => handleAddNode(agentId, actionId)}
                            sx={{ 
                              mr: 1, 
                              mb: 1,
                              borderColor: agentColor,
                              color: agentColor,
                              '&:hover': {
                                borderColor: agentColor,
                                backgroundColor: `${agentColor}10`
                              }
                            }}
                          >
                            {action.name || actionId}
                          </Button>
                        );
                      })}
                    </CardContent>
                  </Card>
                );
              })}
            </Box>
          )}
        </Box>
      </Drawer>
      
      {/* Main content */}
      <Box
        sx={{
          flexGrow: 1,
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          position: 'relative'
        }}
      >
        {/* Top toolbar */}
        <Box
          sx={{
            p: 1,
            borderBottom: '1px solid rgba(0, 0, 0, 0.12)',
            display: 'flex',
            alignItems: 'center'
          }}
        >
          {!drawerOpen && (
            <IconButton onClick={() => setDrawerOpen(true)} size="small" sx={{ mr: 1 }}>
              <ChevronRightIcon />
            </IconButton>
          )}
          
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            {selectedDefinition ? selectedDefinition.name : 'No workflow selected'}
          </Typography>
          
          <Button
            variant="outlined"
            color="primary"
            startIcon={<CodeIcon />}
            onClick={handleToggleJsonView}
            size="small"
            sx={{ mr: 1 }}
          >
            {jsonView ? 'Visual Editor' : 'JSON Editor'}
          </Button>
          
          {selectedNode && (
            <Button
              variant="outlined"
              color="primary"
              startIcon={<EditIcon />}
              onClick={handleEditNode}
              size="small"
              sx={{ mr: 1 }}
            >
              Edit Node
            </Button>
          )}
          
          {selectedNode && (
            <Button
              variant="outlined"
              color="error"
              startIcon={<DeleteIcon />}
              onClick={handleDeleteNode}
              size="small"
            >
              Delete Node
            </Button>
          )}
        </Box>
        
        {/* Main content area */}
        <Box
          sx={{
            flexGrow: 1,
            position: 'relative',
            height: 'calc(100% - 64px)'
          }}
        >
          {loading ? (
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                height: '100%'
              }}
            >
              <Typography>Loading...</Typography>
            </Box>
          ) : error ? (
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                height: '100%'
              }}
            >
              <Typography color="error">{error}</Typography>
            </Box>
          ) : jsonView ? (
            <Box sx={{ p: 2, height: '100%', display: 'flex', flexDirection: 'column' }}>
              <Box sx={{ mb: 2 }}>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleUpdateFromJson}
                  size="small"
                >
                  Update from JSON
                </Button>
              </Box>
              
              <TextField
                label="Workflow JSON"
                multiline
                fullWidth
                rows={20}
                value={workflowJson}
                onChange={(e) => setWorkflowJson(e.target.value)}
                sx={{ flexGrow: 1 }}
              />
            </Box>
          ) : (
            <ReactFlow
              elements={elements}
              onElementClick={onElementClick}
              onElementsRemove={onElementsRemove}
              onConnect={onConnect}
              nodeTypes={nodeTypes}
              defaultZoom={1.5}
              minZoom={0.2}
              maxZoom={4}
              snapToGrid={true}
              snapGrid={[15, 15]}
              deleteKeyCode={46}
            >
              <MiniMap
                nodeStrokeColor={(n) => {
                  if (n.selected) return '#ff0072';
                  return AGENT_COLORS[n.data?.agent] || '#eee';
                }}
                nodeColor={(n) => {
                  return AGENT_COLORS[n.data?.agent] || '#fff';
                }}
              />
              <Controls />
              <Background color="#aaa" gap={16} />
            </ReactFlow>
          )}
        </Box>
      </Box>
      
      {/* Node edit dialog */}
      <Dialog
        open={isEditDialogOpen}
        onClose={() => setIsEditDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Edit Node
          <IconButton
            aria-label="close"
            onClick={() => setIsEditDialogOpen(false)}
            sx={{ position: 'absolute', right: 8, top: 8 }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        
        <DialogContent dividers>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Node Name"
                value={nodeName}
                onChange={(e) => setNodeName(e.target.value)}
                fullWidth
                margin="normal"
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <TextField
                label="Agent"
                value={nodeAgent}
                disabled
                fullWidth
                margin="normal"
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <TextField
                label="Action"
                value={nodeAction}
                disabled
                fullWidth
                margin="normal"
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <TextField
                label="Description"
                value={nodeDescription}
                onChange={(e) => setNodeDescription(e.target.value)}
                fullWidth
                margin="normal"
              />
            </Grid>
            
            <Grid item xs={12}>
              <Typography variant="subtitle1" gutterBottom>
                Parameters
              </Typography>
              
              {/* Render parameters based on action */}
              {nodeAgent && nodeAction && agents[nodeAgent]?.actions[nodeAction]?.parameters ? (
                Object.entries(agents[nodeAgent].actions[nodeAction].parameters).map(([paramName, paramDef]) => (
                  <TextField
                    key={paramName}
                    label={`${paramName}${paramDef.required ? '*' : ''}`}
                    value={nodeParameters[paramName] || ''}
                    onChange={(e) => {
                      setNodeParameters({
                        ...nodeParameters,
                        [paramName]: e.target.value
                      });
                    }}
                    fullWidth
                    margin="normal"
                    helperText={paramDef.description}
                    required={paramDef.required}
                  />
                ))
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No parameters available for this action
                </Typography>
              )}
            </Grid>
          </Grid>
        </DialogContent>
        
        <DialogActions>
          <Button onClick={() => setIsEditDialogOpen(false)} color="primary">
            Cancel
          </Button>
          <Button onClick={handleSaveNode} color="primary" variant="contained">
            Save
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* New workflow dialog */}
      <Dialog
        open={isNewWorkflowDialogOpen}
        onClose={() => setIsNewWorkflowDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          Create New Workflow
          <IconButton
            aria-label="close"
            onClick={() => setIsNewWorkflowDialogOpen(false)}
            sx={{ position: 'absolute', right: 8, top: 8 }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        
        <DialogContent dividers>
          <TextField
            label="Workflow Name"
            value={newWorkflowName}
            onChange={(e) => setNewWorkflowName(e.target.value)}
            fullWidth
            margin="normal"
          />
          
          <TextField
            label="Description"
            value={newWorkflowDescription}
            onChange={(e) => setNewWorkflowDescription(e.target.value)}
            fullWidth
            margin="normal"
            multiline
            rows={3}
          />
        </DialogContent>
        
        <DialogActions>
          <Button onClick={() => setIsNewWorkflowDialogOpen(false)} color="primary">
            Cancel
          </Button>
          <Button 
            onClick={handleCreateWorkflow} 
            color="primary" 
            variant="contained"
            disabled={!newWorkflowName}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Template dialog */}
      <Dialog
        open={isTemplateDialogOpen}
        onClose={() => setIsTemplateDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          Create Workflow from Template
          <IconButton
            aria-label="close"
            onClick={() => setIsTemplateDialogOpen(false)}
            sx={{ position: 'absolute', right: 8, top: 8 }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        
        <DialogContent dividers>
          <FormControl fullWidth margin="normal">
            <InputLabel id="template-select-label">Template</InputLabel>
            <Select
              labelId="template-select-label"
              value={selectedTemplate}
              onChange={(e) => setSelectedTemplate(e.target.value)}
              label="Template"
            >
              {templates.map((template) => (
                <MenuItem key={template} value={template}>
                  {template.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          
          <TextField
            label="Workflow Name (optional)"
            value={newWorkflowName}
            onChange={(e) => setNewWorkflowName(e.target.value)}
            fullWidth
            margin="normal"
            placeholder="Leave blank to use template default"
          />
          
          <TextField
            label="Description (optional)"
            value={newWorkflowDescription}
            onChange={(e) => setNewWorkflowDescription(e.target.value)}
            fullWidth
            margin="normal"
            multiline
            rows={3}
            placeholder="Leave blank to use template default"
          />
        </DialogContent>
        
        <DialogActions>
          <Button onClick={() => setIsTemplateDialogOpen(false)} color="primary">
            Cancel
          </Button>
          <Button 
            onClick={handleCreateFromTemplateConfirm} 
            color="primary" 
            variant="contained"
            disabled={!selectedTemplate}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default WorkflowEditor;