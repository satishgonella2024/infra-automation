// src/api/index.js
import axios from 'axios';

// Determine the proper API URL based on environment
const getApiBaseUrl = () => {
  // Check if we're in a Docker environment (production)
  const hostname = window.location.hostname;
  
  // If we're on the production host (192.168.5.199)
  if (hostname === '192.168.5.199') {
    // In production, the API runs on port 8000
    return 'http://192.168.5.199:8000';
  }
  
  // Local development fallback
  return process.env.REACT_APP_API_URL || 'http://localhost:8000';
};

// Create axios instance with environment-aware config
const api = axios.create({
  baseURL: getApiBaseUrl(),
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000, // 15 seconds timeout
});

// Log the base URL on initialization
console.log('API Service initialized with base URL:', api.defaults.baseURL);

// Add request interceptor for debugging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for debugging
api.interceptors.response.use(
  (response) => {
    console.log(`API Response [${response.status}]: ${response.config.method?.toUpperCase()} ${response.config.url}`);
    return response;
  },
  (error) => {
    if (error.response) {
      console.error('API Response Error:', error.response.status, error.response.data);
    } else if (error.request) {
      console.error('API Response Error: No response received');
    } else {
      console.error('API Error:', error.message);
    }
    return Promise.reject(error);
  }
);

// Helper function to get agent status with fallback
api.getAgentStatus = async function() {
  try {
    // FIXED: Use the correct working endpoint: /status (without /api/ prefix)
    return await this.get('/status');
  } catch (error) {
    console.warn('API /status failed:', error.message);
    
    // Detailed error logging
    if (error.response) {
      console.warn(`Status code: ${error.response.status}`);
    } else if (error.request) {
      console.warn('No response received (likely network issue)');
    }
    
    // Fall back to local mock data
    console.warn('⚠️ Using fallback agent data. Please ensure API is running at', this.defaults.baseURL);
    
    return {
      data: {
        status: "running",
        agents: {
          infrastructure: { 
            id: "infrastructure-agent", 
            name: "Infrastructure Agent", 
            description: "Generates and manages infrastructure code",
            state: "idle" 
          },
          architecture: { 
            id: "architecture-agent", 
            name: "Architecture Agent", 
            description: "Reviews and optimizes architecture",
            state: "idle" 
          },
          security: { 
            id: "security-agent", 
            name: "Security Agent", 
            description: "Analyzes security vulnerabilities",
            state: "idle" 
          },
          cost: { 
            id: "cost-agent", 
            name: "Cost Agent", 
            description: "Optimizes infrastructure costs",
            state: "idle" 
          },
          jira: { 
            id: "jira-agent", 
            name: "Jira Agent", 
            description: "Manages Jira issues and workflows",
            state: "idle" 
          },
          github: { 
            id: "github-agent", 
            name: "GitHub Agent", 
            description: "Manages GitHub repositories and actions",
            state: "idle" 
          },
          kubernetes: { 
            id: "kubernetes-agent", 
            name: "Kubernetes Agent", 
            description: "Manages Kubernetes resources",
            state: "idle" 
          },
          argocd: { 
            id: "argocd-agent", 
            name: "ArgoCD Agent", 
            description: "Handles GitOps deployments",
            state: "idle" 
          },
          security_scanner: { 
            id: "security-scanner-agent", 
            name: "Security Scanner Agent", 
            description: "Performs security scans",
            state: "idle" 
          }
        },
        uptime: 0,
        version: "0.1.0"
      }
    };
  }
};

export default api;