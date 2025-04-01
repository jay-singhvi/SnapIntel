import json
import sys
import re
import os


def extract_code_from_notebook(ipynb_file, exclude_comments=False):
    """
    Extract code cells from Jupyter notebook and return as string.
    Args:
        ipynb_file (str): Path to the input Jupyter notebook (.ipynb) file
        exclude_comments (bool): If True, exclude comments and docstrings
    Returns:
        str: Extracted code content
    """
    # Read the notebook file
    with open(ipynb_file, "r", encoding="utf-8") as f:
        notebook = json.load(f)

    extracted_code = ""
    # Extract code from code cells
    for cell in notebook.get("cells", []):
        if cell.get("cell_type") == "code":
            # Get the source code from the cell
            source = cell.get("source", [])
            # If source is a list, join it together
            if isinstance(source, list):
                source = "".join(source)
            # Process the source code if excluding comments
            if exclude_comments:
                # Remove single-line comments
                source = re.sub(r"^\s*#.*$", "", source, flags=re.MULTILINE)
                # Remove multi-line docstrings (triple quotes)
                source = re.sub(r'"""[\s\S]*?"""', "", source)
                source = re.sub(r"'''[\s\S]*?'''", "", source)
                # Remove empty lines that might be left after removing comments
                source = re.sub(r"\n\s*\n", "\n", source)
            # Add to the extracted code
            if source.strip():  # Only add if there's content left
                extracted_code += source
                # Add a newline at the end if not already present
                if not source.endswith("\n"):
                    extracted_code += "\n"
                extracted_code += "\n"  # Add an extra newline between cells

    return extracted_code


def strip_comments_from_python(input_py_file):
    """
    Remove all comments and docstrings from a Python file and return the cleaned content.
    Args:
        input_py_file (str): Path to the input Python file
    Returns:
        str: Cleaned python code with comments and docstrings removed
    """
    # Read the input file
    with open(input_py_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Remove multi-line docstrings (triple quotes)
    content = re.sub(r'"""[\s\S]*?"""', "", content)
    content = re.sub(r"'''[\s\S]*?'''", "", content)

    # Process the file line by line to handle single-line comments
    lines = content.split("\n")
    processed_lines = []

    # State variables to track if we're inside a string
    in_single_quote = False
    in_double_quote = False
    escaped = False

    for line in lines:
        processed_line = ""
        i = 0
        while i < len(line):
            char = line[i]
            # Handle escape sequences
            if char == "\\" and not escaped:
                escaped = True
                processed_line += char
                i += 1
                continue

            # Handle string boundaries
            if char == '"' and not escaped and not in_single_quote:
                in_double_quote = not in_double_quote
            elif char == "'" and not escaped and not in_double_quote:
                in_single_quote = not in_single_quote

            # Remove comments outside of strings
            if char == "#" and not in_single_quote and not in_double_quote:
                break  # Ignore the rest of the line

            processed_line += char
            escaped = False
            i += 1

        # Add non-empty lines to the result
        if processed_line.strip():
            processed_lines.append(processed_line)

    # Rejoin the lines and clean up any extra blank lines
    cleaned_content = "\n".join(processed_lines)
    cleaned_content = re.sub(
        r"\n\s*\n\s*\n", "\n\n", cleaned_content
    )  # Replace multiple blank lines with one

    return cleaned_content


def is_excluded_path(path, exclude_folder_list=None, exclude_filetype_list=None):
    """
    Check if a path should be excluded based on the exclusion lists.

    Args:
        path (str): The file or folder path to check
        exclude_folder_list (list, optional): List of folder paths to exclude
        exclude_filetype_list (list, optional): List of file extensions to exclude

    Returns:
        bool: True if the path should be excluded, False otherwise
    """
    # Initialize empty lists if None
    exclude_folder_list = exclude_folder_list or []
    exclude_filetype_list = exclude_filetype_list or []

    # Check if path is in excluded folders
    for folder in exclude_folder_list:
        if os.path.normpath(path).startswith(os.path.normpath(folder)):
            return True

    # Check if file has excluded extension
    if os.path.isfile(path):
        file_ext = os.path.splitext(path)[1].lstrip(".")
        if file_ext in exclude_filetype_list:
            return True

    return False


def process_file(file_path, exclude_comments=True):
    """
    Process a file based on its extension and return the cleaned content.
    Args:
        file_path (str): Path to the input file (either .py or .ipynb)
        exclude_comments (bool): Whether to exclude comments from the code
    Returns:
        str: Processed file content with comments removed
    """
    if file_path.endswith(".ipynb"):
        return extract_code_from_notebook(file_path, exclude_comments=exclude_comments)
    elif file_path.endswith(".py"):
        return (
            strip_comments_from_python(file_path)
            if exclude_comments
            else open(file_path, "r", encoding="utf-8").read()
        )
    else:
        # For other files, just return the content as-is
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            return f"[Binary file or unsupported encoding: {file_path}]"


def process_path(
    path,
    output_file,
    exclude_folder_list=None,
    exclude_filetype_list=None,
    exclude_comments=True,
):
    """
    Process a file or recursively process a directory and write content to the output file.

    Args:
        path (str): Path to the file or directory to process
        output_file (file): The open file handle to write to
        exclude_folder_list (list, optional): List of folder paths to exclude
        exclude_filetype_list (list, optional): List of file extensions to exclude
        exclude_comments (bool): Whether to exclude comments from the code
    """
    # Skip if path should be excluded
    if is_excluded_path(path, exclude_folder_list, exclude_filetype_list):
        print(f"Excluded: {path}")
        return

    # Process a single file
    if os.path.isfile(path):
        try:
            # Add the separator and file information
            separator = "=" * 50
            file_header = f"\n{separator}\nFile: {os.path.abspath(path)}\n{separator}\n"
            output_file.write(file_header)

            # Process the file and write to output
            cleaned_content = process_file(path, exclude_comments)
            output_file.write(cleaned_content)
            output_file.write("\n\n")  # Add some space between files

            print(f"Processed file: {path}")
        except Exception as e:
            print(f"Error processing {path}: {str(e)}")

    # Process a directory
    elif os.path.isdir(path):
        try:
            # Add the directory information
            separator = "=" * 50
            dir_header = (
                f"\n{separator}\nDirectory: {os.path.abspath(path)}\n{separator}\n"
            )
            output_file.write(dir_header)

            # Process each item in the directory
            for item in sorted(os.listdir(path)):
                item_path = os.path.join(path, item)
                process_path(
                    item_path,
                    output_file,
                    exclude_folder_list,
                    exclude_filetype_list,
                    exclude_comments,
                )

            print(f"Processed directory: {path}")
        except Exception as e:
            print(f"Error processing directory {path}: {str(e)}")
    else:
        print(f"Path not found or unsupported: {path}")


def main():
    """
    Main function to process input paths and generate the output file.
    """
    # Example command line arguments
    # You can modify this to parse actual command line arguments
    input_file_list = [
        "./company_url_collector/",
        "./data/",
        "flask_Backend.py",
        "test_script.py",
    ]

    # Optional exclusion lists
    exclude_folder_list = [
        "./data/temp/",
        "./venv/",
        "./company_url_collector/src/__pycache__",
    ]
    exclude_filetype_list = []  # e.g., ["txt", "log", "json"]

    # Output file path
    output_file = "Project-File-Content.txt"
    exclude_comments = True

    # Create the combined output content
    with open(output_file, "w", encoding="utf-8") as output:
        for path in input_file_list:
            # Skip empty paths
            if not path:
                continue

            # Process each path (file or directory)
            process_path(
                path,
                output,
                exclude_folder_list,
                exclude_filetype_list,
                exclude_comments,
            )

    print(f"All processed content has been combined into {output_file}")


if __name__ == "__main__":
    # You can implement command line argument parsing here
    # Example: python script.py --input dir1 file1.py --exclude-folders venv temp --exclude-filetypes txt log
    main()
