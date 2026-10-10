import json
from icecream import ic

input_file = "ALL_full.jsonl"
output_file = "ALL_full_jsonl.txt"

processed = 0
skipped = 0

with open(input_file, encoding="utf-8") as infile, \
     open(output_file, "w", encoding="utf-8") as outfile:

    for line_number, line in enumerate(infile, 1):
        line = line.strip()

        if not line:
            continue

        try:
            record = json.loads(line)

            content = record.get("content", "")

            if content:
                outfile.write(content + "\n")

            processed += 1

        except json.JSONDecodeError:
            skipped += 1
            ic("Invalid JSON skipped:", line_number)
            continue

        except Exception as e:
            skipped += 1
            ic("Error skipped:", line_number, str(e))
            continue

ic("================================")
ic("Finished")
ic("Records processed:", processed)
ic("Lines skipped:", skipped)
ic("Output:", output_file)


'''

import json

with open("ALL_full.jsonl", encoding="utf-8") as infile, \
     open("ALL_full_jsonl.txt", "w", encoding="utf-8") as outfile:
    for line in infile:
        line = line.strip()
        if not line:
            continue
        record = json.loads(line)
        outfile.write(record.get("content", "") + "\n")






import json
with open("transcript_full.jsonl", encoding="utf-8") as f:
    first_line = f.readline()
    print(first_line)
    print(json.loads(first_line))






import json

with open("transcript_full.jsonl", encoding="utf-8") as infile, \
     open("transcript_full.txt", "w", encoding="utf-8") as outfile:
    for line in infile:
        line = line.strip()
        if not line:
            continue
        record = json.loads(line)
        outfile.write(record.get("text", "") + "\n")







import json

with open("transcript_full.jsonl", encoding="utf-8") as infile, open("transcript_full_jsonl_.txt", "w") as outfile:
    for line in infile:

        line = line.strip()
        line=line.replace('\\n','\n').replace('\"','"')
        if not line:
            continue
        record = json.loads(line)
        outfile.write(str(record) + "\n")




# Reading a .jsonl file
with open("transcript_full.jsonl") as f:
    records = [json.loads(line) for line in f if line.strip()]

# Writing a .jsonl file
with open("out.jsonl", "w") as f:
    for record in records:
        f.write(json.dumps(record) + "\n")


'''        