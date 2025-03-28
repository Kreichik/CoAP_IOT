import pandas as pd
import numpy as np
import time
from datetime import datetime
import os

# Folder where data will be saved
folder = 'box_data'
if not os.path.exists(folder):
    os.makedirs(folder)


# Generate a new data point based on predefined variables
def generate_random_values():
    # Define the central values for random generation
    bas_temp = 25.1
    soil_temp = 20
    bas_humidity = 52
    light_level = 5

    # Generate random values around the specified values
    air_temp = round(np.random.normal(loc=bas_temp, scale=0.1), 4)  # Around 25 +/- 0.5
    # soil1 = round(np.random.normal(loc=soil_temp, scale=1), 2)  # Soil temperature around 20 +/- 1
    # soil2 = round(np.random.normal(loc=soil_temp, scale=1), 2)
    # soil3 = round(np.random.normal(loc=soil_temp, scale=1), 2)
    # soil4 = round(np.random.normal(loc=soil_temp, scale=1), 2)
    # soil5 = round(np.random.normal(loc=soil_temp, scale=1), 2)
    water_temp = -127  # Can be set or generated similarly
    air_humidity = round(np.random.normal(loc=bas_humidity, scale=0.4), 2)

    # Create timestamp in the required format
    timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')

    # Return the new data row
    return {
        "timestamp": timestamp,
        "device": "both_devices",  # Assuming the device is 'both_devices'
        "soil1": 19,
        "soil2": 19,
        "soil3": 20,
        "soil4": 19.5,
        "soil5": 19.9,
        "water_temperature": water_temp,
        "air_temperature": air_temp,
        "air_humidity": air_humidity,
        "light_level": light_level
    }


# Function to save data to a CSV file
def save_data():
    # Get today's date to generate the filename
    today = datetime.now().strftime('%Y-%m-%d')
    file_path = os.path.join(folder, f"{today}.csv")

    # If the file already exists, load it; otherwise, create a new DataFrame
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
    else:
        df = pd.DataFrame(columns=[
            "timestamp", "device", "soil1", "soil2", "soil3", "soil4", "soil5",
            "water_temperature", "air_temperature", "air_humidity", "light_level"
        ])

    # Generate new random values
    new_data = generate_random_values()

    # Create a new DataFrame for the new data
    new_row_df = pd.DataFrame([new_data])

    # Concatenate the new data row with the existing DataFrame
    df = pd.concat([df, new_row_df], ignore_index=True)

    # Save the DataFrame back to the CSV file
    df.to_csv(file_path, index=False)


# Generate and save data every 5 seconds
while True:
    save_data()
    time.sleep(5)
