"""Randomise the schedule of the 3D contribution workflow.

Previously this read profile-3d.yml, replaced line index 3, and wrote the
result to Profile3D.yml. Both parts were wrong:

  * index 3 is the `schedule:` key, not the cron entry, so the output was
    a `- cron:` list item where a mapping key belonged, with the original
    cron line left dangling underneath it. That is invalid YAML, and it is
    why the workflow failed on every run.
  * writing to Profile3D.yml created a second workflow rather than
    updating the existing one, so the broken copy came back daily even
    after it was deleted.

It now rewrites the cron line in place, in the file it read.
"""
import pathlib
import random
import re

WORKFLOW = pathlib.Path(".github/workflows/profile-3d.yml")
CRON = re.compile(r'^(\s*- cron:\s*")[^"]*(")')

lines = WORKFLOW.read_text().split("\n")

targets = [i for i, line in enumerate(lines) if CRON.match(line)]
if len(targets) != 1:
    raise SystemExit(
        f"expected exactly one cron line in {WORKFLOW}, found {len(targets)}; "
        "refusing to guess rather than corrupt the workflow"
    )

index = targets[0]
current = lines[index]
while True:
    candidate = CRON.sub(rf'\g<1>0 */{random.randint(1, 8)} * * *\g<2>', current)
    if candidate != current:
        break

lines[index] = candidate
WORKFLOW.write_text("\n".join(lines))
print(f"Updated cron: {current.strip()} -> {candidate.strip()}")
