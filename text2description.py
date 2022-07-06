import json
import sys
from colorama import init, Fore, Back
init()

text_file = sys.argv[1]
setting_file = sys.argv[2]

# Lettura testo sinossi
text = open(text_file).read()
text = text.strip()
formatted = text
# formatted = text.replace("\n", "\\n")

print()
print(Fore.GREEN + formatted)
print(Fore.WHITE)
input("Press Enter to save into JSON, ctrl+c to abort...")

# Scrittura JSON
with open(setting_file, 'r', encoding="utf8") as toread:
    data = toread.read()
obj = json.loads(data)
obj['description']['string'] = formatted
with open(setting_file, 'w') as towrite:
    json.dump(obj, towrite, indent=2)

