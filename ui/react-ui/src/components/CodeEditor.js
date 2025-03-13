import React from 'react';
import Editor from '@monaco-editor/react';
import { Box } from '@mui/material';

const CodeEditor = ({ value, onChange, language = 'hcl', height = '300px' }) => {
  const handleEditorChange = (value) => {
    onChange(value);
  };

  return (
    <Box sx={{ border: 1, borderColor: 'divider', borderRadius: 1 }}>
      <Editor
        height={height}
        language={language}
        value={value}
        onChange={handleEditorChange}
        theme="vs-dark"
        options={{
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          fontSize: 14,
          automaticLayout: true,
        }}
      />
    </Box>
  );
};

export default CodeEditor; 