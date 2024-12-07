import json

def python_to_json_string(python_string):
    """
    Converts a Python triple-quoted string into a JSON-compatible string.
    
    Args:
        python_string (str): A Python-formatted string with triple quotes.
    
    Returns:
        str: A JSON-compatible string with escaped characters.
    """
    # Split the string into lines, strip leading/trailing whitespace
    cleaned_string = python_string.strip()
    
    # Replace newlines with `\n` and escape double quotes
    json_compatible_string = cleaned_string.replace("\n", "\\n").replace('"', '\\"')
    
    # Return a JSON-formatted string
    return json.dumps(json_compatible_string)

# Example usage
python_string = """
This is a Python-formatted string
that spans multiple lines.

It is used in Discord bot descriptions!
"""

json_string = python_to_json_string(python_string)

print("Original Python String:")
print(python_string)

print("\nConverted JSON String:")
print(json_string)
