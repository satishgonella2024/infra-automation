import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Collapse,
  IconButton,
  Tooltip,
  Divider
} from '@mui/material';
import {
  Folder as FolderIcon,
  FolderOpen as FolderOpenIcon,
  Description as FileIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  ContentCopy as CopyIcon
} from '@mui/icons-material';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';

// Helper function to determine file language for syntax highlighting
const getFileLanguage = (filename) => {
  const extension = filename.split('.').pop().toLowerCase();
  
  switch (extension) {
    case 'tf':
    case 'tfvars':
      return 'hcl';
    case 'yml':
    case 'yaml':
      return 'yaml';
    case 'json':
      return 'json';
    case 'md':
      return 'markdown';
    case 'sh':
      return 'bash';
    case 'py':
      return 'python';
    case 'js':
      return 'javascript';
    case 'go':
      return 'go';
    default:
      return 'text';
  }
};

// Helper function to copy text to clipboard
const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (err) {
    console.error('Failed to copy text: ', err);
    return false;
  }
};

// Component to display a file with syntax highlighting
const FileContent = ({ filename, content }) => {
  const [copied, setCopied] = useState(false);
  
  const handleCopy = async () => {
    const success = await copyToClipboard(content);
    if (success) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };
  
  return (
    <Box sx={{ mt: 2, position: 'relative' }}>
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        bgcolor: 'grey.900',
        color: 'white',
        p: 1,
        borderTopLeftRadius: 4,
        borderTopRightRadius: 4
      }}>
        <Typography variant="body2" fontFamily="monospace">
          {filename}
        </Typography>
        <Tooltip title={copied ? "Copied!" : "Copy to clipboard"}>
          <IconButton 
            size="small" 
            onClick={handleCopy}
            sx={{ color: copied ? 'success.main' : 'grey.300' }}
          >
            <CopyIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Box>
      <Box sx={{ maxHeight: '400px', overflow: 'auto', borderRadius: '0 0 4px 4px' }}>
        <SyntaxHighlighter
          language={getFileLanguage(filename)}
          style={tomorrow}
          showLineNumbers
          customStyle={{ margin: 0, borderRadius: '0 0 4px 4px' }}
        >
          {content}
        </SyntaxHighlighter>
      </Box>
    </Box>
  );
};

// Recursive component to display the file tree
const FileTreeItem = ({ name, item, path = '', onSelectFile }) => {
  const [open, setOpen] = useState(false);
  const isFolder = typeof item === 'object' && item !== null;
  const fullPath = path ? `${path}/${name}` : name;
  
  const handleToggle = () => {
    setOpen(!open);
  };
  
  const handleFileClick = () => {
    if (!isFolder) {
      onSelectFile(fullPath, item);
    }
  };
  
  return (
    <>
      <ListItem 
        button 
        onClick={isFolder ? handleToggle : handleFileClick}
        sx={{ 
          pl: path.split('/').length + 1,
          borderLeft: isFolder ? 'none' : '1px dashed',
          borderColor: 'divider',
          ml: isFolder ? 0 : 1
        }}
      >
        <ListItemIcon sx={{ minWidth: 36 }}>
          {isFolder ? (
            open ? <FolderOpenIcon color="primary" /> : <FolderIcon color="primary" />
          ) : (
            <FileIcon color="info" />
          )}
        </ListItemIcon>
        <ListItemText 
          primary={name} 
          primaryTypographyProps={{ 
            fontFamily: 'monospace',
            fontSize: '0.9rem'
          }}
        />
        {isFolder && (
          open ? <ExpandLessIcon /> : <ExpandMoreIcon />
        )}
      </ListItem>
      
      {isFolder && (
        <Collapse in={open} timeout="auto" unmountOnExit>
          <List component="div" disablePadding>
            {Object.entries(item).map(([childName, childItem]) => (
              <FileTreeItem 
                key={childName}
                name={childName}
                item={childItem}
                path={fullPath}
                onSelectFile={onSelectFile}
              />
            ))}
          </List>
        </Collapse>
      )}
    </>
  );
};

// Main component
const TerraformModuleTree = ({ moduleFiles }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [selectedContent, setSelectedContent] = useState('');
  
  // Convert flat file structure to tree structure
  const buildFileTree = (files) => {
    const tree = {};
    
    Object.entries(files).forEach(([path, content]) => {
      const parts = path.split('/');
      let current = tree;
      
      parts.forEach((part, index) => {
        if (index === parts.length - 1) {
          // This is a file
          current[part] = content;
        } else {
          // This is a directory
          if (!current[part]) {
            current[part] = {};
          }
          current = current[part];
        }
      });
    });
    
    return tree;
  };
  
  const fileTree = buildFileTree(moduleFiles);
  
  const handleSelectFile = (path, content) => {
    setSelectedFile(path);
    setSelectedContent(content);
  };
  
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Module Structure
      </Typography>
      
      <Box sx={{ display: 'flex', gap: 2, flexDirection: { xs: 'column', md: 'row' } }}>
        <Paper 
          variant="outlined" 
          sx={{ 
            width: { xs: '100%', md: '30%' }, 
            maxHeight: '600px', 
            overflow: 'auto',
            bgcolor: 'background.paper'
          }}
        >
          <List dense component="nav">
            {Object.entries(fileTree).map(([name, item]) => (
              <FileTreeItem 
                key={name}
                name={name}
                item={item}
                onSelectFile={handleSelectFile}
              />
            ))}
          </List>
        </Paper>
        
        <Box sx={{ width: { xs: '100%', md: '70%' } }}>
          {selectedFile ? (
            <FileContent filename={selectedFile} content={selectedContent} />
          ) : (
            <Paper 
              variant="outlined" 
              sx={{ 
                p: 3, 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center',
                height: '200px',
                bgcolor: 'background.paper'
              }}
            >
              <Typography variant="body1" color="text.secondary">
                Select a file from the tree to view its contents
              </Typography>
            </Paper>
          )}
        </Box>
      </Box>
    </Box>
  );
};

export default TerraformModuleTree; 