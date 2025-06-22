import json
import os
import requests
import time
import sys
import argparse
from urllib.parse import unquote

def download_file(url, destination_path):
    """Download a file from a URL to the specified path."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        
        # Write the content to the file
        with open(destination_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        
        print(f"Downloaded: {destination_path}")
        return True
    except Exception as e:
        print(f"Error downloading {url}: {str(e)}")
        return False

def sanitize_filename(filename):
    """Remove or replace characters that are not allowed in filenames."""
    # Replace characters that might cause issues
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename

def main(json_data, base_dir="downloads"):
    """
    Main function to process the JSON data and download all materials.
    
    Args:
        json_data: JSON data containing course and materials information
        base_dir: Base directory for downloads
    """
    # Create the base directory if it doesn't exist
    os.makedirs(base_dir, exist_ok=True)
    
    # Parse the JSON data
    data = json.loads(json_data)
    
    # Process each course
    for course in data.get("data", []):
        course_title = sanitize_filename(course.get("title", "Unknown"))
        course_dir = os.path.join(base_dir, course_title)
        
        # Create directory for the course
        os.makedirs(course_dir, exist_ok=True)
        
        print(f"\nProcessing course: {course_title}")
        
        # Process each material in the course
        for material in course.get("materials", []):
            file_name = sanitize_filename(material.get("fileName", "unknown_file"))
            file_link = material.get("link", "")
            
            # Skip if it's a directory or has no link
            if not file_link or file_link.endswith(course.get("uuid", "")):
                continue
            
            # Full path for the file
            file_path = os.path.join(course_dir, file_name)
            
            # Download the file
            success = download_file(file_link, file_path)
            
            # Add a small delay to avoid overloading the server
            time.sleep(0.5)
    
    print("\nDownload process completed!")

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Download materials recursively from a JSON file.')
    parser.add_argument('json_file', nargs='?', help='Path to the JSON file containing course data')
    parser.add_argument('-o', '--output-dir', default='downloads', help='Output directory for downloaded files (default: downloads)')
    parser.add_argument('--json-string', help='JSON string containing course data (alternative to json_file)')
    
    args = parser.parse_args()
    
    # Get JSON data either from file or direct input
    json_data = None
    
    if args.json_string:
        json_data = args.json_string
    elif args.json_file:
        try:
            with open(args.json_file, 'r', encoding='utf-8') as file:
                json_data = file.read()
        except FileNotFoundError:
            print(f"Error: JSON file '{args.json_file}' not found.")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading JSON file: {str(e)}")
            sys.exit(1)
    else:
        print("Error: Either a JSON file or JSON string must be provided.")
        parser.print_help()
        sys.exit(1)
    
    try:
        # Validate JSON data
        json.loads(json_data)
        
        # Start the download process
        main(json_data, args.output_dir)
        
    except json.JSONDecodeError:
        print("Error: Invalid JSON data. Please check the format.")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        sys.exit(1)
