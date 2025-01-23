# Necessary libraries
from flask import Flask, request, jsonify
from flask_cors import CORS  
import joblib
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from collections import OrderedDict

# Load the model
model_filename = 'co2_emission_random_forest_model.pkl'
model = joblib.load(model_filename)

# Encoding of categorical columns
label_encoders = {
    'Sex': {'Male': 1, 'Female': 0},
    'Pays': {country: idx for idx, country in enumerate([
        'France', 'Germany', 'South Africa', 'Brazil', 'Canada', 
        'India', 'United Kingdom', 'Australia', 'United States', 'China'
    ])},
    'Moyen_de_transport': {transport: idx for idx, transport in enumerate([
        'Bus', 'Voiture (diesel)', 'Train (intercités)', 'Moto', 'Métro', 
        'Train (diesel)', 'Train (électrique)', 'Tramway', 'Voiture (électrique)', 
        'TGV', 'Voiture (essence)'
    ])},
    'Classe_énergétique': {classe: idx for idx, classe in enumerate(['A', 'B', 'C', 'D', 'E', 'F', 'G'])}
}

# Recreate the scaler with the used parameters
scaler = MinMaxScaler()
scaler.min_ = np.array([0, 0, 0, 0, 0, 0, 0, 0])  
scaler.scale_ = np.array([1/1, 1/100, 1/70, 1/3000, 1/10, 1/20000, 1/6, 1/500]) 

# Parameters for denormalizing the target "Kg_CO2_Total_Hebdo"
kg_co2_min = 0  
kg_co2_max = 100  

# Initialize the Flask application
app = Flask(__name__)
CORS(app)  

# Check the API status
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'API is running'})

#  Home page
@app.route('/', methods=['GET'])
def home():
    response = OrderedDict({
        'message': 'Welcome to the CO2 Prediction API!',
        'description': 'This API predicts weekly CO2 emissions based on user input data.',
        'routes': OrderedDict({
            '/health': 'Check the health status of the API.',
            '/predict': 'POST endpoint to make predictions. Requires specific input fields in JSON format.'
        }),
        'example_input': OrderedDict({
            'Sex': 'Male',
            'Âge': 35,
            'Pays': 'France',
            'Consommation_KWh': 1237,
            'Moyen_de_transport': 'Voiture (diesel)',
            'Nombre_de_KM': 1648,
            'Classe_énergétique': 'C',
            'Surface_maison_M2': 150
        })
    })
    return jsonify(response)


#  for making predictions
@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Extract data sent via JSON
        input_data = request.get_json()

        # Required columns
        required_features = [
            'Sex', 'Âge', 'Pays', 'Consommation_KWh',
            'Moyen_de_transport', 'Nombre_de_KM',
            'Classe_énergétique', 'Surface_maison_M2'
        ]
        if not all(feature in input_data for feature in required_features):
            return jsonify({'error': f'Missing features. Required: {required_features}'}), 400

        # Encode categorical data
        try:
            encoded_features = [
                label_encoders['Sex'][input_data['Sex']],
                input_data['Âge'],   # Age left as is
                label_encoders['Pays'][input_data['Pays']],
                input_data['Consommation_KWh'],  # To be normalized
                label_encoders['Moyen_de_transport'][input_data['Moyen_de_transport']],
                input_data['Nombre_de_KM'],  # To be normalized
                label_encoders['Classe_énergétique'][input_data['Classe_énergétique']],
                input_data['Surface_maison_M2']  # To be normalized
            ]
        except KeyError as e:
            return jsonify({'error': f'Invalid categorical value: {e}'}), 400

        # Normalize numerical columns
        features_array = np.array(encoded_features).reshape(1, -1)
        normalized_features = scaler.transform(features_array)

        # Make a prediction
        prediction = model.predict(normalized_features)[0]

        # Denormalize
        real_prediction = prediction * (kg_co2_max - kg_co2_min) + kg_co2_min

        # Return the denormalized result
        return jsonify({'prediction': real_prediction})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Run the application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
