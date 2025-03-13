import React from 'react';
import Editor from '@monaco-editor/react';
import { Box } from '@mui/material';

const ResultViewer = ({ code, language = 'hcl' }) => {
  return (
    <Box sx={{ border: 1, borderColor: 'divider', borderRadius: 1 }}>
      <Editor
        height="300px"
        language={language}
        value={code}
        theme="vs-dark"
        options={{
          readOnly: true,
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          fontSize: 14,
          automaticLayout: true,
        }}
      />
    </Box>
  );
};

export default ResultViewer; 