import React, { useCallback, useEffect, useState } from 'react';
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Panel,
  MarkerType,
  Position,
  Handle,
  useReactFlow,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { IconButton, Tooltip, Box, Typography, Chip } from '@mui/material';
import {
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  CenterFocusStrong as CenterIcon,
  Delete as DeleteIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';

const WorkflowCanvas = ({ agents, onAgentSelect, onWorkflowChange }) => {
  const [selectedNode, setSelectedNode] = useState(null);
  const [selectedEdge, setSelectedEdge] = useState(null);
  const { zoomIn, zoomOut, fitView } = useReactFlow();

  // Convert agents to nodes with initial positions
  const initialNodes = agents.map((agent, index) => ({
    id: agent.id,
    type: 'agentNode',
    position: agent.position || { 
      x: 100 + (index % 3) * 250, 
      y: 100 + Math.floor(index / 3) * 200 
    },
    data: { ...agent },
    draggable: true,
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
  }));

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // Update nodes when agents change
  useEffect(() => {
    const updatedNodes = agents.map((agent, index) => {
      const existingNode = nodes.find(n => n.id === agent.id);
      return {
        id: agent.id,
        type: 'agentNode',
        position: existingNode?.position || { 
          x: 100 + (index % 3) * 250, 
          y: 100 + Math.floor(index / 3) * 200 
        },
        data: { ...agent },
        draggable: true,
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
      };
    });
    setNodes(updatedNodes);
  }, [agents, setNodes]);

  // Notify parent component of workflow changes
  useEffect(() => {
    if (onWorkflowChange) {
      onWorkflowChange({ nodes, edges });
    }
  }, [nodes, edges, onWorkflowChange]);

  const onConnect = useCallback((params) => {
    // Validate connection before adding
    const sourceNode = nodes.find(n => n.id === params.source);
    const targetNode = nodes.find(n => n.id === params.target);
    
    if (sourceNode && targetNode) {
      // Prevent self-connections
      if (params.source === params.target) {
        return;
      }

      // Prevent duplicate connections
      const isDuplicate = edges.some(
        edge => edge.source === params.source && edge.target === params.target
      );
      if (isDuplicate) {
        return;
      }

      // Add the new edge with a unique ID and styling
      const newEdge = {
        ...params,
        id: `${params.source}-${params.target}`,
        type: 'customEdge',
        animated: true,
        style: { stroke: sourceNode.data.color || '#555' },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 20,
          height: 20,
          color: sourceNode.data.color || '#555',
        },
        data: {
          label: 'Flow',
          sourceType: sourceNode.data.type,
          targetType: targetNode.data.type,
        },
      };
      setEdges((eds) => addEdge(newEdge, eds));
    }
  }, [nodes, edges, setEdges]);

  // Handle node drag
  const onNodeDragStop = useCallback((event, node) => {
    // Update node position in the agents array
    const updatedNodes = nodes.map(n => {
      if (n.id === node.id) {
        return {
          ...n,
          position: node.position,
          data: { ...n.data, position: node.position }
        };
      }
      return n;
    });
    setNodes(updatedNodes);
  }, [nodes, setNodes]);

  // Handle node selection
  const onNodeClick = useCallback((event, node) => {
    setSelectedNode(node.id === selectedNode ? null : node.id);
    setSelectedEdge(null);
    if (onAgentSelect) {
      onAgentSelect(node.data);
    }
  }, [selectedNode, onAgentSelect]);

  // Handle edge selection
  const onEdgeClick = useCallback((event, edge) => {
    setSelectedEdge(edge.id === selectedEdge ? null : edge.id);
    setSelectedNode(null);
  }, [selectedEdge]);

  // Handle deletion (nodes or edges)
  const handleDelete = useCallback(() => {
    if (selectedNode) {
      setNodes(nodes.filter(n => n.id !== selectedNode));
      setSelectedNode(null);
    }
    if (selectedEdge) {
      setEdges(edges.filter(e => e.id !== selectedEdge));
      setSelectedEdge(null);
    }
  }, [selectedNode, selectedEdge, setNodes, setEdges, nodes, edges]);

  // Custom edge type
  const edgeTypes = {
    customEdge: ({ id, sourceX, sourceY, targetX, targetY, style, markerEnd, data }) => {
      const edgePath = `M ${sourceX} ${sourceY} C ${sourceX + 50} ${sourceY}, ${targetX - 50} ${targetY}, ${targetX} ${targetY}`;
      const selected = id === selectedEdge;
      
      return (
        <>
          <path
            id={id}
            style={{
              ...style,
              strokeWidth: selected ? 3 : 2,
              stroke: selected ? '#1976d2' : style.stroke,
            }}
            className="react-flow__edge-path"
            d={edgePath}
            markerEnd={markerEnd}
          />
          {data?.label && (
            <text>
              <textPath
                href={`#${id}`}
                style={{ 
                  fontSize: 12,
                  fill: selected ? '#1976d2' : '#666',
                  fontWeight: selected ? 'bold' : 'normal',
                }}
                startOffset="50%"
                textAnchor="middle"
              >
                {data.label}
              </textPath>
            </text>
          )}
        </>
      );
    },
  };

  // Custom node types
  const nodeTypes = {
    agentNode: ({ id, data }) => (
      <div
        style={{
          padding: '15px',
          borderRadius: '8px',
          width: 200,
          fontSize: '13px',
          color: '#222',
          textAlign: 'center',
          borderWidth: 2,
          borderStyle: 'solid',
          borderColor: selectedNode === id ? '#1976d2' : (data.color || '#666'),
          backgroundColor: '#fff',
          boxShadow: selectedNode === id 
            ? '0 0 0 2px #1976d2, 0 4px 8px rgba(0,0,0,0.1)'
            : '0 2px 4px rgba(0,0,0,0.1)',
          cursor: 'pointer',
          transition: 'all 0.2s ease'
        }}
      >
        <Handle 
          type="target" 
          position={Position.Left}
          style={{ 
            background: selectedNode === id ? '#1976d2' : data.color || '#666',
            transition: 'all 0.2s ease'
          }}
        />
        
        <Box sx={{ mb: 1.5 }}>
          <div style={{ 
            color: data.color || '#666',
            marginBottom: '8px',
            transform: 'scale(1.2)'
          }}>
            {data.icon}
          </div>
          <Typography
            variant="subtitle1"
            sx={{
              fontWeight: 'bold',
              color: selectedNode === id ? '#1976d2' : '#222',
              mb: 0.5
            }}
          >
            {data.name}
          </Typography>
          <Chip
            label={data.status}
            size="small"
            color={data.status === 'active' ? 'success' : 'default'}
            variant="outlined"
            icon={<SettingsIcon sx={{ fontSize: '0.8rem' }} />}
            sx={{ 
              height: 24,
              '& .MuiChip-label': { fontSize: '0.75rem' }
            }}
          />
        </Box>

        <Typography
          variant="caption"
          sx={{
            display: 'block',
            color: 'text.secondary',
            px: 1,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap'
          }}
        >
          {data.description || 'No description available'}
        </Typography>

        <Handle 
          type="source" 
          position={Position.Right}
          style={{ 
            background: selectedNode === id ? '#1976d2' : data.color || '#666',
            transition: 'all 0.2s ease'
          }}
        />
      </div>
    ),
  };

  return (
    <div style={{ width: '100%', height: '100%' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        onEdgeClick={onEdgeClick}
        onNodeDragStop={onNodeDragStop}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        deleteKeyCode="Delete"
        multiSelectionKeyCode="Control"
        snapToGrid={true}
        snapGrid={[15, 15]}
      >
        <Controls showInteractive={false} />
        <MiniMap 
          nodeStrokeColor={(n) => selectedNode === n.id ? '#1976d2' : (n.data?.color || '#666')}
          nodeColor={(n) => n.data?.status === 'active' ? '#e6ffe6' : '#fff'}
          maskColor="rgba(255, 255, 255, 0.8)"
        />
        <Background variant="dots" gap={12} size={1} />
        
        {/* Custom Controls Panel */}
        <Panel position="top-right" style={{ margin: '10px', display: 'flex', gap: '8px', flexDirection: 'column' }}>
          <Box sx={{ 
            p: 1.5,
            backgroundColor: 'white', 
            borderRadius: '8px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px'
          }}>
            <Typography variant="subtitle2" sx={{ mb: 1 }}>Canvas Controls</Typography>
            <Box sx={{ display: 'flex', gap: '8px' }}>
              <Tooltip title="Zoom In">
                <IconButton size="small" onClick={() => zoomIn()}>
                  <ZoomInIcon />
                </IconButton>
              </Tooltip>
              <Tooltip title="Zoom Out">
                <IconButton size="small" onClick={() => zoomOut()}>
                  <ZoomOutIcon />
                </IconButton>
              </Tooltip>
              <Tooltip title="Center View">
                <IconButton size="small" onClick={() => fitView()}>
                  <CenterIcon />
                </IconButton>
              </Tooltip>
              <Tooltip title="Delete Selected">
                <IconButton 
                  size="small" 
                  onClick={handleDelete}
                  disabled={!selectedNode && !selectedEdge}
                  color={selectedNode || selectedEdge ? 'error' : 'default'}
                >
                  <DeleteIcon />
                </IconButton>
              </Tooltip>
            </Box>
          </Box>

          <Box sx={{ 
            p: 1.5,
            backgroundColor: 'white', 
            borderRadius: '8px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          }}>
            <Typography variant="subtitle2" sx={{ mb: 1 }}>Instructions</Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '12px' }}>
              <div>🖱️ Drag agents to position them</div>
              <div>🔗 Connect agents by dragging between handles</div>
              <div>⌨️ Press Delete to remove selected items</div>
              <div>⌨️ Hold Control for multi-select</div>
              <div>📐 Nodes snap to grid for alignment</div>
            </Box>
          </Box>
        </Panel>
      </ReactFlow>
    </div>
  );
};

export default WorkflowCanvas; 