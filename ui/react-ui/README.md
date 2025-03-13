# Multi-Agent Infrastructure Automation System - React UI

This is the React-based user interface for the Multi-Agent Infrastructure Automation System. It provides a modern, responsive, and user-friendly interface for interacting with the infrastructure automation API.

## Features

- **Modern UI**: Built with React and Material UI for a sleek, professional look
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Interactive Dashboard**: Real-time overview of system status and recent tasks
- **Infrastructure Generation**: User-friendly form for generating infrastructure
- **Security Review**: Tools for analyzing and fixing security vulnerabilities
- **Task History**: Browse and manage past infrastructure tasks
- **Visualization**: Interactive graphical representations of infrastructure
- **Dark Mode**: Toggle between light and dark themes

## Getting Started

### Prerequisites

- Node.js 16.x or higher
- npm 8.x or higher

### Installation

1. Clone the repository
2. Navigate to the UI directory:
   ```
   cd ui/react-ui
   ```
3. Install dependencies:
   ```
   npm install
   ```

### Development

To start the development server:

```
npm start
```

The application will be available at http://localhost:3000.

### Building for Production

To build the application for production:

```
npm run build
```

The build artifacts will be stored in the `build/` directory.

## Docker

You can also run the UI using Docker:

```
docker build -t infra-automation-ui .
docker run -p 80:80 infra-automation-ui
```

The application will be available at http://localhost.

## Environment Variables

The following environment variables can be set to configure the application:

- `REACT_APP_API_URL`: The URL of the API server (default: http://localhost:8000)
- `REACT_APP_TITLE`: The title of the application (default: Infrastructure Automation)

## License

This project is licensed under the MIT License - see the LICENSE file for details. 