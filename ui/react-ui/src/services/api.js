import axios from 'axios';

// Create an axios instance with default config
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds
});

// API endpoints
export const fetchStatus = async () => {
  const response = await api.get('/status');
  return response.data;
};

export const fetchTasks = async (limit = 10, offset = 0, taskType = null) => {
  let url = `/tasks?limit=${limit}&offset=${offset}`;
  if (taskType) {
    url += `&task_type=${taskType}`;
  }
  const response = await api.get(url);
  return response.data;
};

export const generateInfrastructure = async (data) => {
  const response = await api.post('/infrastructure/generate', data);
  return response.data;
};

export const reviewSecurity = async (data) => {
  const response = await api.post('/security/review', data);
  return response.data;
};

export const getInfrastructureVisualization = async (taskId) => {
  const response = await api.get(`/infrastructure/visualize/${taskId}`);
  return response.data;
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
          break;
        case 500:
          // Server error
          break;
        default:
          // Other errors
          break;
      }
    } else if (error.request) {
      // The request was made but no response was received
      console.error('Network Error:', error.request);
    } else {
      // Something happened in setting up the request
      console.error('Request Error:', error.message);
    }
    
    return Promise.reject(error);
  }
);

export default api; 