import os

def process_text_file(input_file_path):
    """
    Reads a text file line by line and creates separate segN.txt files for each line.
    """
    if not os.path.exists(input_file_path):
        print(f"Error: Input file '{input_file_path}' not found.")
        return

    print(f"Processing '{input_file_path}'...")
    with open(input_file_path, 'r') as f:
        for i, line in enumerate(f):
            # Clean up the line (remove leading/trailing whitespace and newlines)
            cleaned_line = line.strip()
            if cleaned_line: # Only create a file if the line is not empty
                output_file_name = f"seg{i+1}.txt"
                with open(output_file_name, 'w') as out_f:
                    out_f.write(cleaned_line)
                print(f"Created '{output_file_name}' with content: '{cleaned_line}'")
            else:
                print(f"Skipping empty line {i+1}")

if __name__ == "__main__":
    # You can change 'poems.txt' to any other text file you want to process
    process_text_file('poems.txt')
