

# Sydney Housing Price Prediction Application

This project develops a machine learning model to estimate house sale prices in three Sydney suburbs: Blacktown, Parramatta and Randwick.

The final application uses a Random Forest Regressor, which achieved the best cross-validation performance among the three tested regression models.

## Project Files

- `Task 8.1D.ipynb` - Complete data analysis, preprocessing, model development and evaluation.
- `app.py` - Streamlit web application.
- `housing_model_bundle.pkl` - Saved Random Forest model and preprocessing information.
- `requirements.txt` - Required Python packages.

s`yedney_housing_clean.csv` - Dataset
- 
- `data_collection/` - Contains the saved Domain HTML pages and `parse_domain_html.py` used to create the dataset.

## Install Required Packages

Open a terminal in the project folder and run:

    py -m pip install -r requirements.txt

## Run the Application

Run:

    py -m streamlit run app.py

Streamlit will open the application in a web browser.

## How to Use the Application

1. Select the suburb.
2. Enter the number of bedrooms and bathrooms.
3. Enter car spaces and land size, or select Unknown if the information is unavailable.
4. Select the sale method, year and month.
5. Click `Predict Sale Price`.
6. The estimated sale price will be displayed.

## Model and Preprocessing

The application uses the saved Random Forest model.

The same preprocessing used during model development is applied in the application:

- Missing car-space and land-size values are filled using the saved training medians.
- `suburb` and `sale_method` are transformed using the saved One-Hot Encoder.
- The processed input is passed to the Random Forest model.

## Limitations

The model was developed using 112 house sales from Blacktown, Parramatta and Randwick. It should be treated as a decision-support tool rather than an exact property valuat)
