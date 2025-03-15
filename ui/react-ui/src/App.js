import React, { useState, useEffect } from 'react';
import { Routes, Route, useLocation } from 'react-router-dom';
import { Box, CircularProgress } from '@mui/material';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import InfrastructureGenerator from './pages/InfrastructureGenerator';
import SecurityReview from './pages/SecurityReview';
import TaskHistory from './pages/TaskHistory';
import Visualization from './pages/Visualization';
import Settings from './pages/Settings';
import NotFound from './pages/NotFound';
import CostOptimization from './pages/CostOptimization';
import TerraformModules from './pages/TerraformModules';
import Jira from './pages/Jira';
import Confluence from './pages/Confluence';
import GitHub from './pages/GitHub';
import Nexus from './pages/Nexus';
import Kubernetes from './pages/Kubernetes';
import ArgoCD from './pages/ArgoCD';
import WorkflowEditor from './pages/WorkflowEditor';
import Environments from './pages/Environments';
import { fetchStatus } from './services/api';

function App() {
  const [loading, setLoading] = useState(true);
  const [apiStatus, setApiStatus] = useState({
    status: 'offline',
    agents: []
  });
  const location = useLocation();

  useEffect(() => {
    const checkApiStatus = async () => {
      try {
        const status = await fetchStatus();
        // Ensure we have a valid status object
        setApiStatus({
          status: status.status || 'offline',
          agents: Array.isArray(status.agents) ? status.agents : [],
          uptime_seconds: status.uptime_seconds || 0,
          version: status.version || '0.0.0'
        });
      } catch (error) {
        console.error('Failed to fetch API status:', error);
        setApiStatus({
          status: 'offline',
          agents: [],
          uptime_seconds: 0,
          version: '0.0.0'
        });
      } finally {
        setLoading(false);
      }
    };

    checkApiStatus();
    // Poll for status updates every 10 seconds
    const interval = setInterval(checkApiStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    // Add page transition animation
    const content = document.querySelector('.page-content');
    if (content) {
      content.classList.add('fade-in');
      setTimeout(() => {
        content.classList.remove('fade-in');
      }, 500);
    }
  }, [location.pathname]);

  if (loading) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100vh',
          backgroundColor: 'background.default'
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Layout apiStatus={apiStatus}>
      <Box className="page-content" sx={{ p: 3, flexGrow: 1 }}>
        <Routes>
          <Route path="/" element={<Dashboard apiStatus={apiStatus} />} />
          <Route path="/generate" element={<InfrastructureGenerator />} />
          <Route path="/security" element={<SecurityReview />} />
          <Route path="/tasks" element={<TaskHistory />} />
          <Route path="/visualize" element={<Visualization />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/cost" element={<CostOptimization />} />
          <Route path="/modules" element={<TerraformModules />} />
          <Route path="/jira" element={<Jira />} />
          <Route path="/confluence" element={<Confluence />} />
          <Route path="/github" element={<GitHub />} />
          <Route path="/nexus" element={<Nexus />} />
          <Route path="/kubernetes" element={<Kubernetes />} />
          <Route path="/argocd" element={<ArgoCD />} />
          <Route path="/workflow" element={<WorkflowEditor />} />
          <Route path="/environments" element={<Environments />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Box>
    </Layout>
  );
}

export default App; 