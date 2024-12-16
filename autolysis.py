import os
from dotenv import load_dotenv
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import requests
import json
from datetime import datetime
from scipy import stats
import argparse
import sys
import chardet

# Load the .env file from the specified directory
def load_env(file_name):
    dotenv_path = os.path.join("/content/new_folder", file_name)
    load_dotenv(dotenv_path)
    return os.environ.get("AIPROXY_TOKEN")

# Initialize OpenAI API
def init_openai_api():
    api_token = load_env("myfile.env")
    if not api_token:
        raise ValueError("Error: AIPROXY_TOKEN not found in .env file.")
    return {
        "base_url": "https://aiproxy.sanand.workers.dev/openai/v1",
        "headers": {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_token}"
        }
    }

def read_csv(filename):
    try:
        # Detect file encoding
        with open(filename, 'rb') as f:
            raw_data = f.read(10000)  # Read a portion of the file to detect encoding
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            if encoding is None:
                raise ValueError("Could not detect encoding for the file.")

        # Use the detected encoding to read the file
        return pd.read_csv(filename, encoding=encoding)
    except UnicodeDecodeError:
        print(f"Error: Unable to decode {filename} with the detected encoding.")
        print("Attempting fallback encoding...")
        try:
            # Attempt fallback encodings
            return pd.read_csv(filename, encoding='ISO-8859-1')  # Common fallback
        except Exception as fallback_error:
            raise ValueError(f"Fallback decoding failed for {filename}: {fallback_error}")
    except Exception as e:
        raise ValueError(f"General error loading {filename}: {e}")

# Perform detailed statistical analysis on the dataset
def analyze_data(df):
    numeric_data = df.select_dtypes(include=[np.number])
    return {
        "shape": df.shape,
        "columns": df.columns.tolist(),
        "missing_values": df.isnull().sum().to_dict(),
        "summary_statistics": df.describe(include="all").to_dict(),
        "skewness": numeric_data.skew().to_dict(),
        "kurtosis": numeric_data.kurt().to_dict(),
        "correlation_matrix": numeric_data.corr().to_dict() if not numeric_data.empty else {}
    }

# Other functions (e.g., identify_outliers, generate_visualizations, construct_prompt, narrate_story, save_readme)
# remain unchanged.

# Generate unique filename
def generate_unique_filename(filename):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename, extension = os.path.splitext(filename)
    return f"{filename}_{timestamp}{extension}"

# Main script execution
def main(args=None):
    # Use argparse only if not running in an interactive environment
    if args is None:
        args = sys.argv[1:]

    # If running in a notebook, provide a default path for testing
    if not args:
        args = ["/content/new_folder"]

    parser = argparse.ArgumentParser(description="Automated Data Analysis Script")
    parser.add_argument("input", type=str, help="CSV file or folder containing the CSV files")
    
    args = parser.parse_args(args)
    
    # Check if input is a file or folder
    if os.path.isfile(args.input):
        csv_files = [os.path.basename(args.input)]
        os.chdir(os.path.dirname(args.input) or os.getcwd())
    elif os.path.isdir(args.input):
        os.chdir(args.input)
        csv_files = [f for f in os.listdir(args.input) if f.endswith('.csv')]
    else:
        print(f"Error: The input '{args.input}' is neither a valid file nor a folder.")
        return
    
    api = init_openai_api()

    for filename in csv_files:
        filepath = os.path.join(os.getcwd(), filename)
        df = read_csv(filepath)
        analysis = analyze_data(df)
        output_prefix = os.path.splitext(filename)[0]
        charts = generate_visualizations(df, analysis, output_prefix)
        story = narrate_story(api, analysis, charts, filename)
        readme_file = generate_unique_filename(f"README_{output_prefix}.md")
        save_readme(story, charts, readme_file)
        print(f"Analysis completed for {filename}. Check {readme_file} and charts.")

if __name__ == "__main__":
    try:
        if 'ipykernel' in sys.modules:
            # Running in an interactive environment
            main([])
        else:
            # Running as a script
            main()
    except Exception as e:
        print(f"Error during execution: {e}")
