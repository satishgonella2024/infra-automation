# Build stage
FROM node:18-slim as build

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY .npmrc ./

# Install dependencies with specific flags
RUN npm install --legacy-peer-deps --no-optional

# Install specific versions of problematic packages
RUN npm install ajv@8.12.0 ajv-keywords@5.1.0 vis-data@7.1.6 --legacy-peer-deps

# Copy the rest of the application
COPY . .

# Set environment variables to help with the build
ENV NODE_OPTIONS="--max-old-space-size=4096"
ENV GENERATE_SOURCEMAP=false

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built assets from the build stage
COPY --from=build /app/build /usr/share/nginx/html

# Add custom nginx configuration for SPA routing
RUN echo 'server { \
    listen 80; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html index.htm; \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"] 