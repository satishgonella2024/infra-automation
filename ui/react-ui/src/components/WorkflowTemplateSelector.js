// ui/react-ui/src/components/WorkflowTemplateSelector.js
import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Label } from './ui/label';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

export default function WorkflowTemplateSelector() {
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [formData, setFormData] = useState({});
  const [templateSchema, setTemplateSchema] = useState(null);
  
  const navigate = useNavigate();

  useEffect(() => {
    const fetchTemplates = async () => {
      try {
        const response = await api.get('/api/workflows/templates');
        setTemplates(response.data);
        setLoading(false);
      } catch (err) {
        setError('Failed to load templates');
        setLoading(false);
      }
    };
    
    fetchTemplates();
  }, []);

  const handleTemplateChange = async (value) => {
    setSelectedTemplate(value);
    
    try {
      // Fetch template schema
      const response = await api.get(`/api/workflows/templates/${value}/schema`);
      setTemplateSchema(response.data);
      
      // Initialize form data with default values
      const initialData = {};
      Object.entries(response.data.properties).forEach(([key, prop]) => {
        if (prop.default !== undefined) {
          initialData[key] = prop.default;
        }
      });
      
      setFormData(initialData);
    } catch (err) {
      setError('Failed to load template schema');
    }
  };

  const handleInputChange = (key, value) => {
    setFormData({
      ...formData,
      [key]: value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const response = await api.post('/api/workflows/templates', {
        template_type: selectedTemplate,
        parameters: formData
      });
      
      // Navigate to the workflow detail page
      navigate(`/workflows/${response.data.id}`);
    } catch (err) {
      setError('Failed to create workflow');
    }
  };

  if (loading) {
    return <div>Loading templates...</div>;
  }

  if (error) {
    return <div className="text-red-500">{error}</div>;
  }

  return (
    <Card className="w-full max-w-4xl">
      <CardHeader>
        <CardTitle>Create New Workflow</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div>
            <Label htmlFor="template">Select a template</Label>
            <Select onValueChange={handleTemplateChange} value={selectedTemplate}>
              <SelectTrigger id="template">
                <SelectValue placeholder="Select a template" />
              </SelectTrigger>
              <SelectContent>
                {templates.map(template => (
                  <SelectItem key={template} value={template}>
                    {template.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          
          {templateSchema && (
            <form onSubmit={handleSubmit} className="space-y-4">
              {Object.entries(templateSchema.properties).map(([key, prop]) => {
                if (templateSchema.required.includes(key) || prop.default !== undefined) {
                  if (prop.type === 'string' && !prop.enum) {
                    return (
                      <div key={key}>
                        <Label htmlFor={key}>{prop.description || key}</Label>
                        {key.includes('description') ? (
                          <Textarea
                            id={key}
                            value={formData[key] || ''}
                            onChange={e => handleInputChange(key, e.target.value)}
                            placeholder={prop.description}
                            required={templateSchema.required.includes(key)}
                          />
                        ) : (
                          <Input
                            id={key}
                            value={formData[key] || ''}
                            onChange={e => handleInputChange(key, e.target.value)}
                            placeholder={prop.description}
                            required={templateSchema.required.includes(key)}
                          />
                        )}
                      </div>
                    );
                  } else if (prop.type === 'string' && prop.enum) {
                    return (
                      <div key={key}>
                        <Label htmlFor={key}>{prop.description || key}</Label>
                        <Select 
                          onValueChange={value => handleInputChange(key, value)}
                          value={formData[key] || ''}
                        >
                          <SelectTrigger id={key}>
                            <SelectValue placeholder={`Select ${key}`} />
                          </SelectTrigger>
                          <SelectContent>
                            {prop.enum.map(option => (
                              <SelectItem key={option} value={option}>
                                {option}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    );
                  } else if (prop.type === 'boolean') {
                    return (
                      <div key={key} className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          id={key}
                          checked={formData[key] || false}
                          onChange={e => handleInputChange(key, e.target.checked)}
                        />
                        <Label htmlFor={key}>{prop.description || key}</Label>
                      </div>
                    );
                  }
                }
                return null;
              })}
              
              <Button type="submit" className="mt-4">
                Create Workflow
              </Button>
            </form>
          )}
        </div>
      </CardContent>
    </Card>
  );
}