import React, { useState, useEffect } from 'react';
import { Box, CircularProgress, Typography, LinearProgress, Paper, Fade } from '@mui/material';

const LoadingIndicator = ({ message = 'Loading...', showProgress = false, timeout = 30 }) => {
  const [elapsedTime, setElapsedTime] = useState(0);
  const [statusMessage, setStatusMessage] = useState(message);
  const [showTimeoutWarning, setShowTimeoutWarning] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => {
      setElapsedTime(prev => {
        const newTime = prev + 1;
        
        // Update status message based on elapsed time
        if (newTime === 10) {
          setStatusMessage('Still working...');
        } else if (newTime === 20) {
          setStatusMessage('This is taking longer than expected...');
        } else if (newTime === 30) {
          setStatusMessage('Almost there...');
        } else if (newTime === 60) {
          setStatusMessage('Processing complex request...');
        } else if (newTime === 90) {
          setStatusMessage('Still processing. Thank you for your patience...');
        } else if (newTime === 120) {
          setStatusMessage('This is a complex operation. Please continue to wait...');
        } else if (newTime === 180) {
          setStatusMessage('The operation is taking longer than usual...');
        } else if (newTime === 240) {
          setStatusMessage('We\'re working hard on your request...');
          setShowTimeoutWarning(true);
        }
        
        return newTime;
      });
    }, 1000);
    
    return () => clearInterval(timer);
  }, []);

  // Calculate progress percentage (capped at 90% to indicate it's not complete)
  const progressPercentage = Math.min(90, (elapsedTime / timeout) * 100);

  // Format time as mm:ss
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <Paper 
      elevation={2} 
      sx={{ 
        p: 3, 
        borderRadius: 2,
        width: '100%',
        maxWidth: 500,
        backgroundColor: 'rgba(255, 255, 255, 0.9)',
        backdropFilter: 'blur(5px)',
        transition: 'all 0.3s ease'
      }}
    >
      <Box sx={{ 
        display: 'flex', 
        flexDirection: 'column',
        alignItems: 'center', 
        justifyContent: 'center',
        textAlign: 'center'
      }}>
        <CircularProgress 
          size={70} 
          thickness={4} 
          sx={{ 
            mb: 2,
            '& .MuiCircularProgress-circle': {
              strokeLinecap: 'round',
            }
          }} 
        />
        
        <Typography variant="h6" gutterBottom>
          {statusMessage}
        </Typography>
        
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Time elapsed: {formatTime(elapsedTime)}
        </Typography>
        
        {showProgress && (
          <Box sx={{ width: '100%', mt: 2 }}>
            <LinearProgress 
              variant="determinate" 
              value={progressPercentage} 
              sx={{ 
                height: 8, 
                borderRadius: 4,
                '& .MuiLinearProgress-bar': {
                  borderRadius: 4,
                  transition: 'transform 0.4s ease'
                }
              }}
            />
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
              <Typography variant="caption" color="text.secondary">
                0%
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {Math.round(progressPercentage)}%
              </Typography>
              <Typography variant="caption" color="text.secondary">
                100%
              </Typography>
            </Box>
          </Box>
        )}
        
        <Fade in={showTimeoutWarning}>
          <Typography 
            variant="body2" 
            color="warning.main" 
            sx={{ 
              mt: 2, 
              p: 1, 
              border: '1px solid', 
              borderColor: 'warning.light',
              borderRadius: 1,
              backgroundColor: 'warning.lightest',
              maxWidth: '100%'
            }}
          >
            This request is taking longer than expected. It will continue processing in the background even if the UI times out. You can check the task history later for results.
          </Typography>
        </Fade>
      </Box>
    </Paper>
  );
};

export default LoadingIndicator; 