# Use the official Python image as the base image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file to the working directory
COPY requirements.txt ./

# Install the required Python dependencies
RUN pip install -r requirements.txt

# Copy the entire application to the container
COPY . .

# Expose the default Streamlit port
EXPOSE 8501

# Set the entry point to run the Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
