import os
import csv

def get_csv_files(folder_path):
    csv_files = []
    for file in os.listdir(folder_path):
        if file.endswith(".csv"):
            file_path = os.path.join(folder_path, file)
            csv_files.append((file_path, file))
    return csv_files

def rename_files_with_sec(csv_files):
    for file_path, file_name in csv_files:
        if "SEC" in file_name:
            wildcard_index = file_name.index("SEC") + 3
            section_number = file_name[wildcard_index:]
            new_file_name = f"Section {section_number}.csv"
            os.rename(file_path, os.path.join(folder_path, new_file_name))

def extract_lab_section(file_name):
    if "Section" in file_name:
        section_index = file_name.index("Section") + 8  # Move the index to include the section number
        return f"LS {file_name[section_index:section_index + 3]}"
    else:
        return ""

def transform_names_format(csv_file_path):
    lab_section = extract_lab_section(os.path.basename(csv_file_path))
    new_rows = []
    with open(csv_file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            student_info = row.get("Student", "")  # Update to the actual header name
            if "," in student_info:
                last_name, first_name = student_info.split(", ")
                new_name = f"{first_name} {last_name}"
                new_rows.append({"lab section": lab_section, "names": new_name})
    
    return new_rows

def keep_rows_with_lab_section(rows):
    unique_names_with_lab_section = {}
    for row in rows:
        name = row["names"]
        if row["lab section"]:
            unique_names_with_lab_section[name] = row
    
    return list(unique_names_with_lab_section.values())

def create_combined_csv(csv_files, output_file):
    combined_rows = []
    for file_path, _ in csv_files:
        transformed_rows = transform_names_format(file_path)
        combined_rows.extend(transformed_rows)
    
    filtered_rows = keep_rows_with_lab_section(combined_rows)
    
    with open(output_file, 'w', newline='') as combined_csvfile:
        fieldnames = ["lab section", "names"]
        writer = csv.DictWriter(combined_csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(filtered_rows)

if __name__ == "__main__":
    folder_path = os.path.join(os.getcwd(), "data")  # Replace with your actual folder path
    output_folder = os.path.join(os.getcwd(), "output")  # New folder for transformed files
    os.makedirs(output_folder, exist_ok=True)

    csv_files = get_csv_files(folder_path)

    rename_files_with_sec(csv_files)

    output_file = os.path.join(output_folder, "all_students_transformed.csv")
    create_combined_csv(csv_files, output_file)
