FROM php:8.2-cli

# Set working directory
WORKDIR /app

# Copy project files into the container
COPY . /app

# Expose port (Render uses 10000 for PHP apps)
EXPOSE 10000

# Start PHP built-in server
CMD ["php", "-S", "0.0.0.0:10000", "index.php"]
