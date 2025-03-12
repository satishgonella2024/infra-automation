"""
Template Utility Module for Multi-Agent Infrastructure Automation System

This module provides utilities for working with templates for
infrastructure code generation.
"""

import os
import re
import yaml
import jinja2
import logging
from typing import Dict, Any, Optional, List, Union

# Configure logging
logger = logging.getLogger("utils.template")

def render_template(
    template_path: str,
    variables: Dict[str, Any],
    output_path: Optional[str] = None
) -> str:
    """
    Render a Jinja2 template with the provided variables.
    
    Args:
        template_path: Path to the template file
        variables: Dictionary of variables to use in the template
        output_path: Optional path to write the rendered template
        
    Returns:
        The rendered template content
    """
    try:
        # Ensure the template file exists
        if not os.path.exists(template_path):
            logger.error(f"Template file not found: {template_path}")
            raise FileNotFoundError(f"Template file not found: {template_path}")
        
        # Get the template directory
        template_dir = os.path.dirname(template_path)
        template_file = os.path.basename(template_path)
        
        # Set up Jinja2 environment
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True
        )
        
        # Add custom filters if needed
        env.filters["to_yaml"] = lambda x: yaml.dump(x, default_flow_style=False)
        
        # Load and render the template
        template = env.get_template(template_file)
        rendered = template.render(**variables)
        
        # Write to output file if specified
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w") as f:
                f.write(rendered)
            logger.info(f"Rendered template written to: {output_path}")
        
        return rendered
    
    except Exception as e:
        logger.error(f"Error rendering template {template_path}: {str(e)}")
        raise

def load_template_variables(variables_path: str) -> Dict[str, Any]:
    """
    Load variables from a YAML file for template rendering.
    
    Args:
        variables_path: Path to the YAML variables file
        
    Returns:
        Dictionary of variables
    """
    try:
        with open(variables_path, "r") as f:
            variables = yaml.safe_load(f)
        
        if not isinstance(variables, dict):
            raise ValueError(f"Variables file {variables_path} must contain a YAML dictionary")
        
        return variables
    
    except Exception as e:
        logger.error(f"Error loading template variables from {variables_path}: {str(e)}")
        raise

def find_templates(
    templates_dir: str,
    provider: Optional[str] = None,
    template_type: Optional[str] = None
) -> List[str]:
    """
    Find templates matching the given criteria.
    
    Args:
        templates_dir: Base directory for templates
        provider: Optional provider filter (aws, azure, gcp)
        template_type: Optional template type filter (compute, storage, network, etc.)
        
    Returns:
        List of matching template paths
    """
    matching_templates = []
    
    try:
        for root, _, files in os.walk(templates_dir):
            for file in files:
                if file.endswith(".j2") or file.endswith(".jinja2"):
                    file_path = os.path.join(root, file)
                    
                    # Check if the file matches the provider filter
                    if provider and provider.lower() not in file_path.lower():
                        continue
                    
                    # Check if the file matches the template type filter
                    if template_type and template_type.lower() not in file_path.lower():
                        continue
                    
                    matching_templates.append(file_path)
    
    except Exception as e:
        logger.error(f"Error finding templates in {templates_dir}: {str(e)}")
        raise
    
    return matching_templates

def extract_template_metadata(template_path: str) -> Dict[str, Any]:
    """
    Extract metadata from a template file.
    Templates can include metadata in YAML format inside comments at the beginning.
    
    Args:
        template_path: Path to the template file
        
    Returns:
        Dictionary of template metadata
    """
    try:
        with open(template_path, "r") as f:
            content = f.read()
        
        # Look for metadata block in Jinja2 comments
        metadata_match = re.search(r"\{#\s*METADATA\s*\n(.*?)\n\s*#\}", content, re.DOTALL)
        
        if metadata_match:
            metadata_yaml = metadata_match.group(1)
            metadata = yaml.safe_load(metadata_yaml)
            
            if not isinstance(metadata, dict):
                logger.warning(f"Invalid metadata format in {template_path}")
                return {}
            
            return metadata
        
        return {}
    
    except Exception as e:
        logger.error(f"Error extracting metadata from {template_path}: {str(e)}")
        return {}

def create_template(
    template_content: str,
    output_path: str,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Create a new template file with optional metadata.
    
    Args:
        template_content: The content of the template
        output_path: Path to write the template
        metadata: Optional metadata to include in the template
        
    Returns:
        The path to the created template
    """
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Add metadata if provided
        if metadata:
            metadata_yaml = yaml.dump(metadata, default_flow_style=False)
            template_content = f"{{% comment %}}\nMETADATA\n{metadata_yaml}\n{{% endcomment %}}\n\n{template_content}"
        
        # Write the template
        with open(output_path, "w") as f:
            f.write(template_content)
        
        logger.info(f"Created template at: {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"Error creating template at {output_path}: {str(e)}")
        raise