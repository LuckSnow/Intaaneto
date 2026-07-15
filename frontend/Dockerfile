FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install exactly the dependency graph in package-lock.json
RUN npm ci

# Copy project files
COPY . .

# Expose port
EXPOSE 5173

# Start development server
CMD ["npm", "run", "dev", "--", "--host"]
