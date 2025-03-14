import React, { useState } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  CircularProgress,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Settings as SettingsIcon,
  Check as CheckIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import axios from '../api';

const AgentPanel = ({ agent, onUpdate }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [config, setConfig] = useState(agent.config || {});

  // Get configuration fields based on agent type
  const getConfigFields = () => {
    switch (agent.type) {
      case 'jira':
        return [
          { name: 'url', label: 'Jira URL', type: 'text' },
          { name: 'username', label: 'Username', type: 'text' },
          { name: 'api_token', label: 'API Token', type: 'password' },
          { name: 'project_key', label: 'Project Key', type: 'text' },
        ];
      case 'confluence':
        return [
          { name: 'url', label: 'Confluence URL', type: 'text' },
          { name: 'username', label: 'Username', type: 'text' },
          { name: 'api_token', label: 'API Token', type: 'password' },
          { name: 'space_key', label: 'Space Key', type: 'text' },
        ];
      case 'github':
        return [
          { name: 'token', label: 'GitHub Token', type: 'password' },
          { name: 'owner', label: 'Repository Owner', type: 'text' },
          { name: 'repo', label: 'Repository Name', type: 'text' },
        ];
      case 'nexus':
        return [
          { name: 'url', label: 'Nexus URL', type: 'text' },
          { name: 'username', label: 'Username', type: 'text' },
          { name: 'password', label: 'Password', type: 'password' },
          { name: 'repository', label: 'Repository', type: 'text' },
        ];
      case 'kubernetes':
        return [
          { name: 'kubeconfig', label: 'Kubeconfig Path', type: 'text' },
          { name: 'context', label: 'Context', type: 'text' },
          { name: 'namespace', label: 'Namespace', type: 'text' },
        ];
      case 'argocd':
        return [
          { name: 'url', label: 'ArgoCD URL', type: 'text' },
          { name: 'token', label: 'Auth Token', type: 'password' },
          { name: 'project', label: 'Project', type: 'text' },
        ];
      case 'vault':
        return [
          { name: 'url', label: 'Vault URL', type: 'text' },
          { name: 'token', label: 'Token', type: 'password' },
          { name: 'namespace', label: 'Namespace', type: 'text' },
        ];
      case 'security_scanner':
        return [
          { name: 'checkov_path', label: 'Checkov Path', type: 'text' },
          { name: 'trivy_path', label: 'Trivy Path', type: 'text' },
          { name: 'scan_targets', label: 'Scan Targets', type: 'text' },
        ];
      default:
        return [];
    }
  };

  // Handle configuration changes
  const handleConfigChange = (field, value) => {
    setConfig(prev => ({
      ...prev,
      [field]: value
    }));
  };

  // Test agent configuration
  const handleTestConfig = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post(`/api/agents/${agent.id}/test`, { config });
      if (response.data.success) {
        onUpdate({ ...agent, config, status: 'configured' });
      } else {
        setError(response.data.message || 'Configuration test failed');
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to test configuration');
    } finally {
      setLoading(false);
    }
  };

  // Save agent configuration
  const handleSave = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.put(`/api/agents/${agent.id}/config`, { config });
      onUpdate({ ...agent, config, status: 'configured' });
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to save configuration');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      {/* Agent Status */}
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
        <Chip
          label={agent.status}
          color={agent.status === 'configured' ? 'success' : 'default'}
          icon={agent.status === 'configured' ? <CheckIcon /> : <SettingsIcon />}
          variant="outlined"
        />
        {error && (
          <Chip
            label={error}
            color="error"
            icon={<ErrorIcon />}
            variant="outlined"
            onDelete={() => setError(null)}
          />
        )}
      </Box>

      {/* Configuration Form */}
      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="subtitle1">Configuration</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Box component="form" sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {getConfigFields().map((field) => (
              <TextField
                key={field.name}
                label={field.label}
                type={field.type}
                value={config[field.name] || ''}
                onChange={(e) => handleConfigChange(field.name, e.target.value)}
                fullWidth
                size="small"
                variant="outlined"
              />
            ))}
          </Box>
        </AccordionDetails>
      </Accordion>

      {/* Actions */}
      <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
        <Button
          variant="outlined"
          onClick={handleTestConfig}
          disabled={loading}
          startIcon={loading ? <CircularProgress size={20} /> : <SettingsIcon />}
        >
          Test Configuration
        </Button>
        <Button
          variant="contained"
          onClick={handleSave}
          disabled={loading}
          startIcon={loading ? <CircularProgress size={20} /> : <CheckIcon />}
        >
          Save Changes
        </Button>
      </Box>

      {/* Documentation */}
      <Accordion sx={{ mt: 3 }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="subtitle1">Documentation</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Typography variant="body2" color="text.secondary">
            {getAgentDocumentation(agent.type)}
          </Typography>
        </AccordionDetails>
      </Accordion>
    </Box>
  );
};

// Helper function to get agent documentation
const getAgentDocumentation = (type) => {
  const docs = {
    jira: 'Configure Jira integration by providing your Jira Cloud instance URL, username, and API token. The API token can be generated from your Jira account settings.',
    confluence: 'Set up Confluence integration with your instance URL, username, and API token. Make sure to specify the space key where content will be managed.',
    github: 'GitHub integration requires a personal access token with appropriate repository permissions. Specify the repository owner and name to connect.',
    nexus: 'Connect to your Nexus repository manager by providing the server URL, credentials, and target repository name.',
    kubernetes: 'Kubernetes integration uses your kubeconfig file. Specify the path to the kubeconfig and optionally set a specific context and namespace.',
    argocd: 'ArgoCD integration needs your ArgoCD server URL and an authentication token. Specify the project name to manage applications.',
    vault: 'HashiCorp Vault integration requires the Vault server URL, authentication token, and optionally a namespace for enterprise installations.',
    security_scanner: 'Configure security scanning by specifying paths to Checkov and Trivy executables. Add scan targets as a comma-separated list.',
  };
  return docs[type] || 'No documentation available for this agent type.';
};

export default AgentPanel; 