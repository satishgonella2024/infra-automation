#!/bin/bash

# Script to set up and start environment a8374274-290e-4c31-beed-51c41a7b74b1

mkdir -p /home/satish/infra-automation/data/environments/a8374274-290e-4c31-beed-51c41a7b74b1
mkdir -p /home/satish/infra-automation/data/environments/a8374274-290e-4c31-beed-51c41a7b74b1/dashboard

cat > /home/satish/infra-automation/data/environments/a8374274-290e-4c31-beed-51c41a7b74b1/docker-compose.yml << 'EOL'
version: '3.8'

services:
  jira:
    image: atlassian/jira-software:latest
    environment:
      - ATL_JDBC_URL=jdbc:postgresql://db:5432/jira
      - ATL_JDBC_USER=jira
      - ATL_JDBC_PASSWORD=${JIRA_DB_PASSWORD}
    ports:
      - "8080:8080"
    volumes:
      - jira-data:/var/atlassian/application-data/jira
    depends_on:
      - db

  gitlab:
    image: gitlab/gitlab-ce:latest
    environment:
      GITLAB_OMNIBUS_CONFIG: |
        external_url 'http://gitlab.local'
    ports:
      - "8929:80"
      - "2224:22"
    volumes:
      - gitlab-config:/etc/gitlab
      - gitlab-logs:/var/log/gitlab
      - gitlab-data:/var/opt/gitlab

  db:
    image: postgres:13
    environment:
      - POSTGRES_PASSWORD=${DB_ROOT_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data

  dashboard:
    image: nginx:latest
    ports:
      - "80:80"
    volumes:
      - ./dashboard:/usr/share/nginx/html

volumes:
  jira-data:
  gitlab-config:
  gitlab-logs:
  gitlab-data:
  postgres-data:

EOL

cat > /home/satish/infra-automation/data/environments/a8374274-290e-4c31-beed-51c41a7b74b1/.env << 'EOL'
ENVIRONMENT_ID=a8374274-290e-4c31-beed-51c41a7b74b1
ENVIRONMENT_NAME=wordpress-env
DB_ROOT_PASSWORD=password_4816d3e2
JIRA_DB_PASSWORD=jira_password_310170dd
CONFLUENCE_DB_PASSWORD=confluence_password_aecbc75a
VAULT_ROOT_TOKEN=vault_token_9b1808fa

EOL

cat > /home/satish/infra-automation/data/environments/a8374274-290e-4c31-beed-51c41a7b74b1/dashboard/index.html << 'EOL'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Environment Dashboard</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f5f7fa;
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        header {
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            text-align: center;
            margin-bottom: 30px;
        }
        h1 {
            margin: 0;
            font-size: 2.5em;
        }
        .environment-info {
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            padding: 20px;
            margin-bottom: 30px;
        }
        .tools-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .tool-card {
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            padding: 20px;
            transition: transform 0.2s;
        }
        .tool-card:hover {
            transform: translateY(-5px);
        }
        .tool-header {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
        }
        .tool-icon {
            width: 40px;
            height: 40px;
            margin-right: 15px;
        }
        .tool-name {
            font-size: 1.5em;
            margin: 0;
        }
        .tool-description {
            color: #666;
            margin-bottom: 15px;
        }
        .tool-link {
            display: inline-block;
            background-color: #3498db;
            color: white;
            padding: 10px 15px;
            border-radius: 4px;
            text-decoration: none;
            font-weight: bold;
            transition: background-color 0.2s;
        }
        .tool-link:hover {
            background-color: #2980b9;
        }
        .credentials {
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            padding: 20px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f8f9fa;
        }
        .status {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 4px;
            font-weight: bold;
        }
        .status-running {
            background-color: #2ecc71;
            color: white;
        }
        .status-creating {
            background-color: #f39c12;
            color: white;
        }
        .status-failed {
            background-color: #e74c3c;
            color: white;
        }
        footer {
            text-align: center;
            margin-top: 50px;
            padding: 20px;
            color: #7f8c8d;
        }
    </style>
</head>
<body>
    <header>
        <h1>Environment Dashboard</h1>
        <p>Your complete development environment</p>
    </header>
    
    <div class="container">
        <div class="environment-info">
            <h2>Environment Information</h2>
            <p><strong>Name:</strong> <span id="env-name">wordpress-env</span></p>
            <p><strong>Type:</strong> <span id="env-type">development</span></p>
            <p><strong>Status:</strong> <span id="env-status" class="status status-creating">creating</span></p>
            <p><strong>Created:</strong> <span id="env-created">2025-03-15T05:33:59.098901</span></p>
            <p><strong>ID:</strong> <span id="env-id">a8374274-290e-4c31-beed-51c41a7b74b1</span></p>
        </div>
        
        <h2>Available Tools</h2>
        <div class="tools-grid" id="tools-container">
            <!-- Tool cards will be inserted here -->
            
            <div class="tool-card">
                <div class="tool-header">
                    <img src="https://wac-cdn.atlassian.com/assets/img/favicons/atlassian/favicon.png" alt="Jira" class="tool-icon">
                    <h3 class="tool-name">Jira</h3>
                </div>
                <p class="tool-description">Issue tracking and project management</p>
                <a href="#" target="_blank" class="tool-link">Open Jira</a>
            </div>
            
            <div class="tool-card">
                <div class="tool-header">
                    <img src="https://about.gitlab.com/images/press/logo/png/gitlab-icon-rgb.png" alt="GitLab" class="tool-icon">
                    <h3 class="tool-name">GitLab</h3>
                </div>
                <p class="tool-description">Git repository management and CI/CD</p>
                <a href="#" target="_blank" class="tool-link">Open GitLab</a>
            </div>
            
        </div>
        
        <div class="credentials">
            <h2>Access Credentials</h2>
            <table>
                <thead>
                    <tr>
                        <th>Tool</th>
                        <th>Username</th>
                        <th>Password/Token</th>
                    </tr>
                </thead>
                <tbody id="credentials-table">
                    <!-- Credentials will be inserted here -->
                    
                </tbody>
            </table>
        </div>
    </div>
    
    <footer>
        <p>Powered by Multi-Agent Infrastructure Automation System</p>
    </footer>
</body>
</html> 
EOL

# Modify ports to avoid conflicts
sed -i 's/"8080:8080"/"8092:8080"/' /home/satish/infra-automation/data/environments/a8374274-290e-4c31-beed-51c41a7b74b1/docker-compose.yml
sed -i 's/"8929:80"/"8941:80"/' /home/satish/infra-automation/data/environments/a8374274-290e-4c31-beed-51c41a7b74b1/docker-compose.yml
sed -i 's/"80:80"/"8093:80"/' /home/satish/infra-automation/data/environments/a8374274-290e-4c31-beed-51c41a7b74b1/docker-compose.yml

# Start the environment
cd /home/satish/infra-automation/data/environments/a8374274-290e-4c31-beed-51c41a7b74b1
docker-compose --project-name env-a8374274 up -d

# Update the environment status
curl -X PUT http://localhost:8000/api/onboarding/environments/a8374274-290e-4c31-beed-51c41a7b74b1 -H "Content-Type: application/json" -d '{
  "status": "running"
}'
