# Use official Python image
FROM python:3.10-slim

# Environment variables
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy only requirements first for caching
COPY requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy all app code
COPY ./app /app/app
COPY ./scripts /app/scripts
COPY ./alembic.ini /app/alembic.ini
COPY ./alembic /app/alembic

# Expose port FastAPI will run on
EXPOSE 8000

# Default command to run FastAPI using uvicorn
# Use 'sh -c' so we can read the $PORT variable.
CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"