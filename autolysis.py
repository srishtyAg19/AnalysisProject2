import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import requests
import json
import numpy as np
from tabulate import tabulate
from scipy import stats
from datetime import datetime
from dotenv import load_dotenv

# Define the folder path (update if needed)
folder_path = r"/content/csv_files"  

# Define the .env file path
dotenv_path = os.path.join(folder_path, "myfile.env")

# Check if the .env file exists
if not os.path.exists(dotenv_path):
    print("Files in the directory:", os.listdir(folder_path))
    raise FileNotFoundError(f"The .env file was not found at {dotenv_path}.")

# Load the .env file
load_dotenv(dotenv_path, encoding='utf-16')

# Access the token from the .env file
api_proxy_token = os.getenv("AI_PROXY")

if not api_proxy_token:
    raise ValueError("AI_PROXY token not found in the .env file.")

print("AI_PROXY token loaded successfully.")

# Base URL for the API
api_proxy_base_url = "https://aiproxy.sanand.workers.dev/"

def read_csv(filename):
    """Read the CSV file and return a DataFrame, trying different encodings."""
    for encoding in ['utf-8', 'latin1', 'utf-16']: 
        try:
            df = pd.read_csv(filename, encoding=encoding)
            print(f"Dataset loaded with {encoding}: {filename}")
            return df
        except UnicodeDecodeError:
            print(f"Encoding {encoding} failed for {filename}. Trying next encoding...")
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            exit()
    print(f"Could not load {filename} with any of the tried encodings.")
    exit()

def analyze_data(df):
    """Perform basic analysis on the dataset."""
    analysis = {
        "shape": df.shape,
        "columns": df.columns.tolist(),
        "missing_values": df.isnull().sum().to_dict(),
        "summary_statistics": df.describe(include="all").to_dict()
    }
    return analysis

def visualize_data(df, output_prefix):
    """Generate visualizations for the dataset."""
    charts = []
    
    # Correlation Heatmap (if numeric data exists)
    numeric_columns = df.select_dtypes(include=["number"]).columns
    if len(numeric_columns) > 0:
        plt.figure(figsize=(14, 12))
        heatmap = sns.heatmap(df[numeric_columns].corr(), annot=True, cmap="coolwarm", fmt=".2f")
        heatmap.set_title("Correlation Heatmap")
        heatmap_file = generate_unique_filename(f"{output_prefix}_heatmap.png")
        plt.savefig(heatmap_file, dpi=300)
        charts.append(heatmap_file)
        plt.close()
        print(f"Generated heatmap: {heatmap_file}") # Debugging: Print generated file path

    # Bar Plot for the first categorical column
    categorical_columns = df.select_dtypes(include=["object"]).columns
    if len(categorical_columns) > 0:
        plt.figure(figsize=(14, 8))
        top_categories = df[categorical_columns[0]].value_counts().head(10)
        top_categories.sort_values().plot(kind="barh", color="skyblue")
        plt.title(f"Top 10 {categorical_columns[0]} Categories")
        barplot_file = generate_unique_filename(f"{output_prefix}_barplot.png")
        plt.savefig(barplot_file, dpi=300)
        charts.append(barplot_file)
        plt.close()
        print(f"Generated barplot: {barplot_file}") # Debugging: Print generated file path

    return charts

def narrate_story(analysis, charts, filename):
    """Use GPT-4o-Mini to narrate a story about the analysis."""
    summary_prompt = f"""
    I analyzed a dataset from {filename}. It has the following details:
    - Shape: {analysis['shape']}
    - Columns: {analysis['columns']}
    - Missing Values: {analysis['missing_values']}
    - Summary Statistics: {analysis['summary_statistics']}

    Write a short summary of the dataset, key insights, and recommendations. Refer to the charts where necessary.
    """
    url = f"{api_proxy_base_url}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_proxy_token}"
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": summary_prompt}],
        "temperature": 0.7
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        return f"Story generation failed: {e}"

def save_markdown(story, charts, output_file):
    """Save the narrated story and chart references to a README.md file."""
    with open(output_file, "w") as f:
        f.write("# Analysis Report\n\n")
        f.write(story + "\n\n")
        for chart in charts:
            f.write(f"![Chart](./{chart})\n")

def save_table(df, output_file):
    """Save the dataframe as a formatted table in the README.md file."""
    table = tabulate(df.head(), headers='keys', tablefmt='pipe', showindex=False)
    with open(output_file, "a") as f:
        f.write("\n## Sample Data\n\n")
        f.write(table + "\n")

def generate_unique_filename(filename):
    """Generate a unique filename by appending a timestamp."""
    if os.path.exists(filename):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename, extension = os.path.splitext(filename)
        filename = f"{filename}_{timestamp}{extension}"
    return filename

def main():
    # Change to the specified folder
    try:
        os.chdir(folder_path)
    except Exception as e:
        print(f"Error accessing folder {folder_path}: {e}")
        return
    
    # Automatically process all CSV files in the folder
    csv_files = [f for f in os.listdir() if f.endswith('.csv')]
    
    if not csv_files:
        print("No CSV files found in the directory.")
        return
    
    for filename in csv_files:
        print(f"Processing {filename}...")

        # Load dataset
        df = read_csv(filename)
        
        # Analyze dataset
        analysis = analyze_data(df)
        
        # Visualize data
        output_prefix = filename.split(".")[0]
        charts = visualize_data(df, output_prefix)
        
        # Narrate story
        story = narrate_story(analysis, charts, filename)
        
        # Save README.md
        readme_file = generate_unique_filename(f"README_{output_prefix}.md")
        save_markdown(story, charts, readme_file)
        
        # Save Sample Data Table
        save_table(df, readme_file)

        print(f"Analysis completed for {filename}. Check {readme_file} and charts.")

if __name__ == "__main__":
    main()

