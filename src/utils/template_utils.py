"""
Template utilities for infrastructure automation.

This module provides functions for loading and rendering templates.
"""

import os
import re
from typing import Optional, Dict, Any
from jinja2 import Environment, FileSystemLoader, Template

# Initialize Jinja2 environment
template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
env = Environment(
    loader=FileSystemLoader(template_dir),
    trim_blocks=True,
    lstrip_blocks=True
)

def load_template(template_name: str) -> Template:
    """
    Load a Jinja2 template from the templates directory.
    
    Args:
        template_name: Name of the template file
        
    Returns:
        Jinja2 Template object
    """
    return env.get_template(template_name)

def render_template(template_name: str, **context: Dict[str, Any]) -> str:
    """
    Load and render a Jinja2 template with the given context.
    
    Args:
        template_name: Name of the template file
        **context: Variables to pass to the template
        
    Returns:
        Rendered template as a string
    """
    template = load_template(template_name)
    return template.render(**context)

def extract_code_from_text(text: str) -> Optional[str]:
    """
    Extract code from text that may be wrapped in backticks.
    
    Args:
        text: Text that may contain code blocks
        
    Returns:
        Extracted code or None if no code block found
    """
    # Try to find code block with language specifier
    match = re.search(r'```(?:\w+)?\s*([\s\S]*?)\s*```', text)
    if match:
        return match.group(1).strip()
    
    # Try to find code block without language specifier
    match = re.search(r'```([\s\S]*?)```', text)
    if match:
        return match.group(1).strip()
    
    # If no code blocks found, return the original text stripped
    return text.strip()
