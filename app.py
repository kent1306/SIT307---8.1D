import streamlit as st
import joblib
import pandas as pd
import numpy as np
st.title("Sydney Housing Price Predictor")

st.write(
    "This application uses the trained Random Forest model "
    "to estimate house sale prices."
)

bundle = joblib.load("housing_model_bundle.pkl")

model = bundle["model"]
encoder = bundle["encoder"]
car_median = bundle["car_median"]
land_median = bundle["land_median"]
numeric_features = bundle["numeric_features"]
categorical_features = bundle["categorical_features"]
encoded_feature_names = bundle["encoded_feature_names"]

st.success("The trained model was loaded successfully.")
st.subheader("Enter Property Information")

suburb = st.selectbox(
    "Suburb",
    ["Blacktown", "Parramatta", "Randwick"]
)

bedrooms = st.number_input(
    "Bedrooms",
    min_value=1,
    max_value=10,
    value=3
)

bathrooms = st.number_input(
    "Bathrooms",
    min_value=1,
    max_value=10,
    value=2
)

car_unknown = st.checkbox("Car Spaces Unknown")

if car_unknown:
    car_spaces = np.nan
else:
    car_spaces = st.number_input(
        "Car Spaces",
        min_value=0,
        max_value=10,
        value=2
    )

land_unknown = st.checkbox("Land Size Unknown")

if land_unknown:
    land_size = np.nan
else:
    land_size = st.number_input(
        "Land Size (m²)",
        min_value=0.0,
        value=500.0
    )

sale_method = st.selectbox(
    "Sale Method",
    [
        "at auction",
        "by private treaty",
        "prior to auction"
    ]
)

sale_year = st.selectbox(
    "Sale Year",
    [2025, 2026]
)

sale_month = st.selectbox(
    "Sale Month",
    list(range(1, 13))
)
if st.button("Predict Sale Price"):

    input_data = pd.DataFrame({
        "suburb": [suburb],
        "bedrooms": [bedrooms],
        "bathrooms": [bathrooms],
        "car_spaces": [car_spaces],
        "land_size_m2": [land_size],
        "sale_method": [sale_method],
        "sale_year": [sale_year],
        "sale_month": [sale_month]
    })

    encoded_data = encoder.transform(
        input_data[categorical_features]
    )

    encoded_df = pd.DataFrame(
        encoded_data,
        columns=encoded_feature_names
    )

    model_input = pd.concat(
        [
            input_data[numeric_features].reset_index(drop=True),
            encoded_df
        ],
        axis=1
    )

    predicted_price = model.predict(model_input)[0]

    st.success(
        f"Estimated Sale Price: ${predicted_price:,.0f}"
    )