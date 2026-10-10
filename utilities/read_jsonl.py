import json

with open("transcript_full.jsonl", encoding="utf-8") as infile, \
     open("transcript_full.txt", "w", encoding="utf-8") as outfile:
    for line in infile:
        line = line.strip()
        if not line:
            continue
        record = json.loads(line)
        outfile.write(record.get("content", "") + "\n")




'''

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