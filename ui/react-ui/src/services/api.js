import axios from 'axios';

// Create an axios instance with default config
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://192.168.5.199:8000',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // Reduce default timeout to 30 seconds for better user experience
});

// Add retry functionality
const createAxiosWithRetry = (instance, maxRetries = 3) => {
  instance.interceptors.response.use(undefined, async (error) => {
    const { config, message } = error;
    
    // Don't retry on 404 errors
    if (error.response && error.response.status === 404) {
      return Promise.reject(error);
    }
    
    // Only retry on timeout errors, network errors, and 5xx errors if we haven't reached max retries
    const shouldRetry = (
      (message.includes('timeout') || 
       message.includes('Network Error') || 
       (error.response && error.response.status >= 500)) && 
      config && 
      (!config.__retryCount || config.__retryCount < maxRetries)
    );
    
    if (shouldRetry) {
      // Increase retry count
      config.__retryCount = config.__retryCount || 0;
      config.__retryCount += 1;
      
      // Increase timeout for each retry
      config.timeout = config.timeout * 1.5;
      
      // Create new promise to handle retry
      return new Promise((resolve) => {
        console.log(`Retrying request (${config.__retryCount}/${maxRetries}), increasing timeout to ${config.timeout}ms`);
        setTimeout(() => resolve(instance(config)), 1000 * config.__retryCount); // Progressive backoff
      });
    }
    
    return Promise.reject(error);
  });
  
  return instance;
};

// Apply retry functionality to our API instance
createAxiosWithRetry(api);

// API endpoints
export const fetchStatus = async () => {
  try {
    const response = await api.get('/api/status', {
      timeout: 30000, // 30 second timeout
      retries: 2,     // Allow 2 retries
      retryDelay: 1000 // Wait 1 second between retries
    });
    
    // Ensure we have a valid status object with the correct structure
    const data = response.data;
    return {
      status: data.status || 'running',
      agents: Object.entries(data.agents || {}).map(([key, agent]) => ({
        name: agent.name || key,
        status: agent.state || 'unknown'
      })),
      uptime_seconds: data.uptime || 0,
      version: data.version || '0.0.0'
    };
  } catch (error) {
    console.error('Error fetching status:', error);
    // Return a more detailed offline status
    return {
      status: 'offline',
      error: error.message,
      version: '0.0.0',
      uptime_seconds: 0,
      agents: [],
      tasks_count: 0,
      last_task_time: null
    };
  }
};

export const fetchTasks = async (limit = 10, offset = 0, taskType = null) => {
  try {
    let url = `/tasks?limit=${limit}&offset=${offset}`;
    if (taskType) {
      url += `&task_type=${taskType}`;
    }
    const response = await api.get(url);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch tasks:', error);
    return []; // Return empty array on error
  }
};

export const generateInfrastructure = async (data) => {
  // Use a longer timeout for infrastructure generation (5 minutes)
  const response = await api.post('/infrastructure/generate', data, {
    timeout: 300000, // 5 minutes
    __retryCount: 0 // Initialize retry count
  });
  return response.data;
};

export const reviewSecurity = async (data) => {
  // Use a longer timeout for security reviews (3 minutes)
  const response = await api.post('/security/review', data, {
    timeout: 180000, // 3 minutes
    __retryCount: 0 // Initialize retry count
  });
  return response.data;
};

export const getInfrastructureVisualization = async (taskId) => {
  try {
    const response = await api.get(`/infrastructure/visualize/${taskId}`);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch visualization:', error);
    
    // Log more specific error for debugging
    if (error.response && error.response.status === 404) {
      console.log('Visualization endpoint not found. Using sample data instead.');
    }
    
    // Return sample visualization data if the endpoint is not available
    return {
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
  }
};

export const optimizeCosts = async (data) => {
  try {
    const response = await api.post('/infrastructure/optimize-costs', {
      code: data.infrastructure_code,
      cloud_provider: data.cloud_provider,
      iac_type: data.iac_type
    });
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const fetchTerraformModule = async (taskId) => {
  try {
    const response = await api.get(`/terraform/module/${taskId}`);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch Terraform module:', error);
    throw error;
  }
};

export const downloadTerraformModule = async (taskId) => {
  try {
    // Use blob response type to handle binary data
    const response = await api.get(`/terraform/module/${taskId}/download`, {
      responseType: 'blob'
    });
    
    // Create a download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    
    // Get filename from Content-Disposition header or use default
    const contentDisposition = response.headers['content-disposition'];
    let filename = 'terraform-module.zip';
    
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="(.+)"/);
      if (filenameMatch && filenameMatch[1]) {
        filename = filenameMatch[1];
      }
    }
    
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    
    return true;
  } catch (error) {
    console.error('Failed to download Terraform module:', error);
    throw error;
  }
};

// Environment API endpoints
export const fetchEnvironments = async (userId = null) => {
  try {
    let url = '/api/onboarding/environments';
    if (userId) {
      url += `?user_id=${userId}`;
    }
    const response = await api.get(url);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch environments:', error);
    return { environments: [], count: 0 }; // Return empty array on error
  }
};

export const fetchEnvironmentDetails = async (environmentId) => {
  try {
    const response = await api.get(`/api/onboarding/environments/${environmentId}`);
    return response.data;
  } catch (error) {
    console.error(`Failed to fetch environment ${environmentId}:`, error);
    throw error;
  }
};

export const fetchEnvironmentCredentials = async (environmentId) => {
  try {
    const response = await api.get(`/api/onboarding/environments/${environmentId}/credentials`);
    return response.data;
  } catch (error) {
    console.error(`Failed to fetch credentials for environment ${environmentId}:`, error);
    throw error;
  }
};

export const createEnvironment = async (environmentData) => {
  try {
    const response = await api.post('/api/onboarding/new-environment', environmentData);
    return response.data;
  } catch (error) {
    console.error('Failed to create environment:', error);
    throw error;
  }
};

export const deleteEnvironment = async (environmentId) => {
  try {
    const response = await api.delete(`/api/onboarding/environments/${environmentId}`);
    return response.data;
  } catch (error) {
    console.error(`Failed to delete environment ${environmentId}:`, error);
    throw error;
  }
};

// Error handling interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle specific error codes
    if (error.response) {
      // Server responded with a status code outside the 2xx range
      console.error('API Error:', error.response.data);
      
      // You can handle specific status codes here
      switch (error.response.status) {
        case 401:
          // Unauthorized - handle authentication
          break;
        case 403:
          // Forbidden - handle permissions
          break;
        case 404:
          // Not found
          console.log(`Resource not found: ${error.config.url}`);
          break;
        case 500:
          // Server error
          console.log('Server error occurred. The operation might still be processing.');
          break;
        default:
          // Other errors
          break;
      }
    } else if (error.request) {
      // The request was made but no response was received
      console.error('Network Error:', error.request);
      
      // Add more specific error message for timeout
      if (error.code === 'ECONNABORTED') {
        console.log('Request timed out. The operation may still be processing in the background.');
        error.message = 'Request timed out. The operation is taking longer than expected. The system will continue processing your request in the background. You can check the task history later for results.';
      } else {
        console.log('Network error occurred. Please check your connection.');
        error.message = 'Network error occurred. Please check your connection and try again.';
      }
    } else {
      // Something happened in setting up the request
      console.error('Request Error:', error.message);
    }
    
    return Promise.reject(error);
  }
);

export default api; 