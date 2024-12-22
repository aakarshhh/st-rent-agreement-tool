# Project Setup Instructions

This document provides instructions on how to set up the project using Docker and an alternative local environment if Docker is not available.

---

## Prerequisites

- **Docker** (for Docker setup)
- **Python 3.9+** (for local setup)
- **pip** (Python package manager)

---

## Docker Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/aakarshhh/st-rent-agreement-tool.git
   cd st-rent-agreement-tool
   ```
2. **Environment Variables**:
   - Before running Docker, ensure the following environment variables are configured: Replace `YourOpenAIKey` in the `docker-compose.yml` file with your actual OpenAI API key.

3. **Build and run the Docker container**:
   - Ensure you have a `Dockerfile` and `docker-compose.yml` file in the project root.
   - Run the following commands:
     ```bash
     docker-compose up --build
     ```

4. **Access the Streamlit application**:
   - Open your browser and navigate to:
     ```
     http://localhost:8501
     ```


---

## Local Environment Setup

If Docker is not available, follow these steps to set up a local environment:

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd <repository-folder>
   ```

2. **Set up a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables**:
   - Create a `.env` file in the project root and add the following:
     ```env
     OPEN_AI_API_KEY=YourOpenAIKey
     ```

5. **Run the Streamlit app**:
   ```bash
   streamlit run app.py --server.port=8501 --server.address=0.0.0.0
   ```

6. **Access the application**:
   - Open your browser and navigate to:
     ```
     http://localhost:8501
     ```

---

## Notes

- Ensure you have the correct OpenAI API key and replace `YourOpenAIKey` in the instructions above.
- If you encounter any issues, check the logs for detailed error messages and confirm that all dependencies are installed correctly.

---

Feel free to reach out if you have any questions or need additional support!

akss4567@gmail.com