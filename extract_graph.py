# extract_graph.py
import re, collections, sys

ENTER = re.compile(r'\[DEBUG\] → (\S+) IN')
EXIT  = re.compile(r'\[DEBUG\] ← (\S+) OUT')
LINK  = re.compile(r'\[DEBUG\] ↔ (\S+) → (\S+)')

edges = collections.Counter()
stack = []

for line in sys.stdin:
    # Cross‑service link
    m = LINK.search(line)
    if m:
        src, dst = m.group(1), m.group(2)
        edges[(src, dst)] += 1
        continue

    # Normal function entry – build intra‑service edges
    m = ENTER.search(line)
    if m:
        cur = m.group(1)
        if stack:
            edges[(stack[-1], cur)] += 1
        stack.append(cur)
        continue

    # Function exit – pop the stack
    if EXIT.search(line) and stack:
        stack.pop()

# Output Mermaid diagram
print("graph TD")
for (src, dst), cnt in edges.items():
    print(f"    {src} -->|{cnt}| {dst}")
