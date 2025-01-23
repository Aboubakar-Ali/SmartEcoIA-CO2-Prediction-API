#  image Python officielle
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy necessary files into the container
COPY app.py /app/app.py
COPY co2_emission_random_forest_model.pkl /app/co2_emission_random_forest_model.pkl

# Install dependencies
RUN pip install --no-cache-dir flask joblib numpy scikit-learn==1.3.2 flask-cors

# port
EXPOSE 5000

# Command to run the application
CMD ["python", "app.py"]
