# Hunt Memory

This folder is reserved for **structured memory** - the optional "recall system" for Level 3+ hunting.

## Level 1-2: Persistent/Augmented - Use Grep

At early maturity levels, your `hunts/` folder IS your memory. Before starting a new hunt, search through past hunt notes:

```bash
# Find hunts by TTP
grep -l "T1110.001" ../hunts/*.md

# Find by behavior
grep -i "brute force" ../hunts/*.md

# Find by technology
grep -i "powershell" ../hunts/*.md

# Find by application
grep -i "active directory" ../hunts/*.md

# Find by keyword
grep -i "privilege escalation" ../hunts/*.md

# Find what worked
grep "Decision: Accept" ../hunts/*.md
```

**No additional files needed.** The discipline of reviewing old hunts before starting new ones is what creates memory.

## Level 3+: Autonomous/Coordinated - Add Structure When Grep Fails

When you have 50+ hunts or need to support multiple parallel hunts, grep becomes painful. At that point, create structured memory:

### Option 1: JSON Index
```json
{
  "hunts": [
    {
      "hunt_id": "H-0001",
      "ttps": ["T1059.001", "T1027"],
      "decision": "accept",
      "lessons": ["baseline automation critical"]
    }
  ]
}
```

### Option 2: SQLite Database
Queryable, supports complex filters, still portable as a single file.

### Option 3: Markdown Index
Human-readable table linking to run notes with key metadata.

## Why Wait?

Early optimization kills simplicity. Build the habit of reviewing past hunts first. Add structure only when complexity demands it.

The goal: **Make recall easy, not fancy.**
