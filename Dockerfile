# Use the official Python image as a base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

COPY Dockerfile /app/Dockerfile
COPY requirements.txt /app/requirements.txt
COPY config_.py /app/config_.py
COPY webserver_app.py /app/webserver_app.py
COPY static /app/static
COPY templates /app/templates

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=webserver_app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

# Start the Flask application
CMD ["bash", "-c", "flask run"]


