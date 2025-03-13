import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  IconButton,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  InputAdornment,
  CircularProgress,
  Alert,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Snackbar,
  Tabs,
  Tab
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Search as SearchIcon,
  Visibility as VisibilityIcon,
  Code as CodeIcon,
  Security as SecurityIcon,
  History as HistoryIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Storage as StorageIcon,
  Download as DownloadIcon
} from '@mui/icons-material';
import { fetchTasks, fetchTerraformModule, downloadTerraformModule } from '../services/api';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';
import TerraformModuleTree from '../components/TerraformModuleTree';

// Safe clipboard copy function
const copyToClipboard = async (text) => {
  try {
    // Check if the Clipboard API is available
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(text);
      console.log('Text copied to clipboard using Clipboard API');
      return true;
    } else {
      // Fallback for browsers that don't support the Clipboard API
      const success = fallbackCopyToClipboard(text);
      return success;
    }
  } catch (err) {
    console.error('Failed to copy text: ', err);
    // Try fallback method if primary method fails
    const success = fallbackCopyToClipboard(text);
    return success;
  }
};

const fallbackCopyToClipboard = (text) => {
  try {
    // Create a temporary textarea element
    const textArea = document.createElement('textarea');
    textArea.value = text;
    
    // Make the textarea out of viewport
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    
    // Select and copy the text
    textArea.focus();
    textArea.select();
    const successful = document.execCommand('copy');
    
    // Clean up
    document.body.removeChild(textArea);
    
    if (successful) {
      console.log('Text copied to clipboard using fallback');
      return true;
    } else {
      console.error('Fallback clipboard copy failed');
      return false;
    }
  } catch (err) {
    console.error('Fallback clipboard copy failed: ', err);
    return false;
  }
};

function TaskHistory() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [totalTasks, setTotalTasks] = useState(0);
  const [taskType, setTaskType] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTask, setSelectedTask] = useState(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [copySuccess, setCopySuccess] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  const [moduleLoading, setModuleLoading] = useState(false);
  const [moduleError, setModuleError] = useState(null);
  const [moduleData, setModuleData] = useState(null);
  const [downloadSuccess, setDownloadSuccess] = useState(false);

  useEffect(() => {
    loadTasks();
  }, [page, rowsPerPage, taskType]);

  const loadTasks = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetchTasks(rowsPerPage, page * rowsPerPage, taskType);
      setTasks(response);
      // In a real app, the API would return the total count
      // This is a placeholder for demonstration
      setTotalTasks(100);
    } catch (err) {
      console.error('Failed to fetch tasks:', err);
      setError('Failed to load tasks. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleTaskTypeChange = (event) => {
    setTaskType(event.target.value);
    setPage(0);
  };

  const handleSearchChange = (event) => {
    setSearchQuery(event.target.value);
  };

  const handleRefresh = () => {
    loadTasks();
  };

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const handleViewTask = async (task) => {
    setSelectedTask(task);
    setDialogOpen(true);
    setActiveTab(0);
    
    // If this is a terraform module task, fetch the module data
    if (task.type === 'terraform_module_generation' && task.status === 'completed') {
      setModuleLoading(true);
      setModuleError(null);
      
      try {
        const data = await fetchTerraformModule(task.id || task.task_id);
        setModuleData(data);
      } catch (err) {
        console.error('Failed to fetch module data:', err);
        setModuleError('Failed to load module data. Please try again later.');
      } finally {
        setModuleLoading(false);
      }
    }
  };

  const handleDownloadModule = async () => {
    if (!selectedTask) return;
    
    try {
      await downloadTerraformModule(selectedTask.id || selectedTask.task_id);
      setDownloadSuccess(true);
    } catch (err) {
      console.error('Failed to download module:', err);
      alert('Failed to download module. Please try again later.');
    }
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
  };

  const getTaskTypeIcon = (type) => {
    switch (type) {
      case 'infrastructure_generation':
        return <CodeIcon />;
      case 'security_review':
        return <SecurityIcon />;
      case 'architecture_review':
        return <HistoryIcon />;
      case 'terraform_module_generation':
        return <StorageIcon />;
      default:
        return <HistoryIcon />;
    }
  };

  const getTaskTypeColor = (type) => {
    switch (type) {
      case 'infrastructure_generation':
        return 'primary';
      case 'security_review':
        return 'secondary';
      case 'architecture_review':
        return 'info';
      case 'terraform_module_generation':
        return 'success';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon color="success" />;
      case 'failed':
        return <ErrorIcon color="error" />;
      case 'in_progress':
        return <CircularProgress size={20} />;
      case 'pending':
        return <WarningIcon color="warning" />;
      default:
        return null;
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const formatTaskType = (type) => {
    if (!type) return 'Unknown';
    return type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const formatTaskId = (id) => {
    if (!id) return 'N/A';
    return typeof id === 'string' && id.length > 8 ? `${id.substring(0, 8)}...` : id;
  };

  return (
    <Box className="slide-in-up">
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Task History
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

      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
          <FormControl sx={{ minWidth: 200 }}>
            <InputLabel id="task-type-label">Task Type</InputLabel>
            <Select
              labelId="task-type-label"
              value={taskType}
              label="Task Type"
              onChange={handleTaskTypeChange}
            >
              <MenuItem value="">All Types</MenuItem>
              <MenuItem value="infrastructure_generation">Infrastructure Generation</MenuItem>
              <MenuItem value="security_review">Security Review</MenuItem>
              <MenuItem value="architecture_review">Architecture Review</MenuItem>
              <MenuItem value="terraform_module_generation">Terraform Module</MenuItem>
            </Select>
          </FormControl>
          
          <TextField
            label="Search"
            variant="outlined"
            value={searchQuery}
            onChange={handleSearchChange}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
          />
        </Box>

        {error ? (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        ) : (
          <TableContainer>
            <Table sx={{ minWidth: 650 }}>
              <TableHead>
                <TableRow>
                  <TableCell>ID</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Description</TableCell>
                  <TableCell>Created At</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={6} align="center">
                      <CircularProgress />
                    </TableCell>
                  </TableRow>
                ) : tasks.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} align="center">
                      No tasks found
                    </TableCell>
                  </TableRow>
                ) : (
                  tasks.map((task, index) => (
                    <TableRow key={task.id || task.task_id || index} hover>
                      <TableCell>{formatTaskId(task.id || task.task_id)}</TableCell>
                      <TableCell>
                        <Chip
                          icon={getTaskTypeIcon(task.type)}
                          label={formatTaskType(task.type)}
                          color={getTaskTypeColor(task.type)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>{task.description || 'No description'}</TableCell>
                      <TableCell>{formatDate(task.timestamp)}</TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          {getStatusIcon(task.status)}
                          <Typography variant="body2" sx={{ ml: 1 }}>
                            {task.status ? task.status.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) : 'Unknown'}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell align="right">
                        <Tooltip title="View Details">
                          <IconButton onClick={() => handleViewTask(task)}>
                            <VisibilityIcon />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        )}
        
        <TablePagination
          rowsPerPageOptions={[5, 10, 25]}
          component="div"
          count={totalTasks}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </Paper>

      {/* Task Details Dialog */}
      <Dialog
        open={dialogOpen}
        onClose={handleCloseDialog}
        maxWidth="lg"
        fullWidth
      >
        {selectedTask && (
          <>
            <DialogTitle>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                {getTaskTypeIcon(selectedTask.type)}
                <Typography variant="h6" sx={{ ml: 1 }}>
                  {formatTaskType(selectedTask.type)} Details
                </Typography>
              </Box>
            </DialogTitle>
            <DialogContent dividers>
              {selectedTask.type === 'terraform_module_generation' ? (
                <>
                  <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
                    <Tabs value={activeTab} onChange={handleTabChange}>
                      <Tab label="Details" />
                      <Tab label="Module Files" />
                    </Tabs>
                  </Box>
                  
                  {activeTab === 0 ? (
                    <>
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle1">Task ID:</Typography>
                        <Typography variant="body1">{formatTaskId(selectedTask.id || selectedTask.task_id)}</Typography>
                      </Box>
                      
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle1">Description:</Typography>
                        <Typography variant="body1">
                          {selectedTask.request?.task || selectedTask.description || 'No description'}
                        </Typography>
                      </Box>
                      
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle1">Created At:</Typography>
                        <Typography variant="body1">{formatDate(selectedTask.timestamp || selectedTask.created_at)}</Typography>
                      </Box>
                      
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle1">Status:</Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          {getStatusIcon(selectedTask.status)}
                          <Typography variant="body1" sx={{ ml: 1 }}>
                            {selectedTask.status ? selectedTask.status.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) : 'Unknown'}
                          </Typography>
                        </Box>
                      </Box>
                      
                      {selectedTask.result && selectedTask.result.thoughts && (
                        <Box sx={{ mb: 2 }}>
                          <Typography variant="subtitle1" gutterBottom>Agent's Thoughts:</Typography>
                          <Typography variant="body2">{selectedTask.result.thoughts}</Typography>
                        </Box>
                      )}
                      
                      {selectedTask.result && selectedTask.result.metadata && (
                        <Box sx={{ mb: 2 }}>
                          <Typography variant="subtitle1" gutterBottom>Module Metadata:</Typography>
                          <Paper variant="outlined" sx={{ p: 2, bgcolor: 'background.paper' }}>
                            <pre style={{ margin: 0, overflow: 'auto' }}>
                              {JSON.stringify(selectedTask.result.metadata, null, 2)}
                            </pre>
                          </Paper>
                        </Box>
                      )}
                    </>
                  ) : (
                    <>
                      {moduleLoading ? (
                        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                          <CircularProgress />
                        </Box>
                      ) : moduleError ? (
                        <Alert severity="error" sx={{ mb: 2 }}>
                          {moduleError}
                        </Alert>
                      ) : moduleData && moduleData.result && moduleData.result.module_files ? (
                        <TerraformModuleTree moduleFiles={moduleData.result.module_files} />
                      ) : (
                        <Alert severity="info" sx={{ mb: 2 }}>
                          No module files available or module generation is still in progress.
                        </Alert>
                      )}
                    </>
                  )}
                </>
              ) : (
                <>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle1">Task ID:</Typography>
                    <Typography variant="body1">{formatTaskId(selectedTask.id || selectedTask.task_id)}</Typography>
                  </Box>
                  
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle1">Description:</Typography>
                    <Typography variant="body1">{selectedTask.description || 'No description'}</Typography>
                  </Box>
                  
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle1">Created At:</Typography>
                    <Typography variant="body1">{formatDate(selectedTask.timestamp)}</Typography>
                  </Box>
                  
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle1">Status:</Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      {getStatusIcon(selectedTask.status)}
                      <Typography variant="body1" sx={{ ml: 1 }}>
                        {selectedTask.status ? selectedTask.status.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) : 'Unknown'}
                      </Typography>
                    </Box>
                  </Box>
                  
                  {selectedTask.result && selectedTask.result.code && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle1" gutterBottom>Generated Code:</Typography>
                      <Box sx={{ maxHeight: '300px', overflow: 'auto', borderRadius: 1 }}>
                        <SyntaxHighlighter
                          language={selectedTask.result.iac_type === 'terraform' ? 'hcl' : selectedTask.result.iac_type === 'ansible' ? 'yaml' : 'groovy'}
                          style={tomorrow}
                          showLineNumbers
                        >
                          {selectedTask.result.code}
                        </SyntaxHighlighter>
                      </Box>
                    </Box>
                  )}
                  
                  {selectedTask.result && selectedTask.result.thoughts && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle1" gutterBottom>Agent's Thoughts:</Typography>
                      <Typography variant="body2">{selectedTask.result.thoughts}</Typography>
                    </Box>
                  )}
                </>
              )}
            </DialogContent>
            <DialogActions>
              <Button onClick={handleCloseDialog}>Close</Button>
              
              {selectedTask.type === 'terraform_module_generation' && 
               selectedTask.status === 'completed' && (
                <Button
                  variant="contained"
                  color="primary"
                  startIcon={<DownloadIcon />}
                  onClick={handleDownloadModule}
                >
                  Download Module
                </Button>
              )}
              
              {selectedTask.type !== 'terraform_module_generation' && 
               selectedTask.result && selectedTask.result.code && (
                <Button
                  onClick={async () => {
                    try {
                      const success = await copyToClipboard(selectedTask.result.code);
                      if (success) {
                        setCopySuccess(true);
                      } else {
                        // If both methods fail, show a manual copy dialog
                        alert('Automatic copy failed. Please manually select and copy the code.');
                      }
                    } catch (error) {
                      console.error('Copy operation failed:', error);
                      alert('Automatic copy failed. Please manually select and copy the code.');
                    }
                  }}
                >
                  Copy Code
                </Button>
              )}
            </DialogActions>
          </>
        )}
      </Dialog>

      <Snackbar
        open={copySuccess}
        autoHideDuration={3000}
        onClose={() => setCopySuccess(false)}
        message="Code copied to clipboard"
      />
      
      <Snackbar
        open={downloadSuccess}
        autoHideDuration={3000}
        onClose={() => setDownloadSuccess(false)}
        message="Module downloaded successfully"
      />
    </Box>
  );
}

export default TaskHistory; 