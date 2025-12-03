# How to Record a Killer ATHF Demo GIF

## Step 1: Install Recording Tools

**Option A: asciinema + agg (Recommended - Best Quality)**
```bash
brew install asciinema
brew install agg
```

**Option B: vhs (Modern alternative)**
```bash
brew install vhs
```

## Step 2: Prepare Your Terminal

1. **Set a clean prompt:**
   ```bash
   export PS1="$ "
   ```

2. **Use a good terminal size:**
   - Resize terminal to 100 columns × 30 rows
   - Or run: `printf '\e[8;30;100t'`

3. **Set a nice theme:**
   - Use a high-contrast theme (Solarized Dark, Dracula, Nord)
   - Make sure text is readable

4. **Clear the terminal:**
   ```bash
   clear
   ```

## Step 3: Record the Demo

### Using asciinema (Recommended)

```bash
# 1. Start recording
asciinema rec athf-demo.cast

# 2. Run the demo script
./scripts/record-demo.sh

# 3. Stop recording (Ctrl+D or type 'exit')

# 4. Convert to GIF with good settings
agg \
  --speed 1.5 \
  --font-size 16 \
  --theme dracula \
  athf-demo.cast \
  assets/demo.gif
```

### Using vhs (Alternative)

Create a vhs tape file and let it record automatically:

```bash
vhs scripts/demo.tape
```

(I can create the tape file if you want this option)

## Step 4: Optimize the GIF

**If the GIF is too large:**

```bash
# Option 1: Reduce colors with gifsicle
brew install gifsicle
gifsicle -O3 --colors 256 assets/demo.gif -o assets/demo-optimized.gif

# Option 2: Use ffmpeg
brew install ffmpeg
ffmpeg -i assets/demo.gif -vf "fps=10,scale=800:-1:flags=lanczos" -c:v gif assets/demo-optimized.gif
```

**Target size:** Under 5MB for GitHub (preferably 2-3MB)

## Step 5: Preview

```bash
# macOS: Open in default viewer
open assets/demo.gif

# Or use browser
open -a "Google Chrome" assets/demo.gif
```

## Pro Tips for a Great Recording

### Before Recording:
- ✅ Close all other terminal windows
- ✅ Disable terminal bell/notifications
- ✅ Make sure terminal size is consistent
- ✅ Test the script once to see timing
- ✅ Have good lighting (if recording screen)

### During Recording:
- ✅ Don't rush - let commands breathe
- ✅ Pause at key outputs so viewers can read
- ✅ Keep it under 60 seconds
- ✅ Don't show errors or restarts

### After Recording:
- ✅ Watch the playback before converting
- ✅ Re-record if anything looks off
- ✅ Test GIF loads in browser
- ✅ Check file size (under 5MB)

## What Makes a Great Demo

**DO:**
- Show the full workflow (init → create → list → validate)
- Highlight the Rich terminal output (colors, tables)
- Keep it fast-paced but readable
- End with a clear call-to-action

**DON'T:**
- Show errors or failed commands
- Make it too long (60 seconds max)
- Use tiny fonts or poor contrast
- Include setup/configuration details

## Quick Command Reference

```bash
# Install tools
brew install asciinema agg

# Record
asciinema rec demo.cast

# Run your demo script
./scripts/record-demo.sh

# Convert to GIF
agg --speed 1.5 --font-size 16 demo.cast assets/demo.gif

# Optimize if needed
gifsicle -O3 --colors 256 assets/demo.gif -o assets/demo.gif
```

## Alternative: Record Screen Video

If terminal recording doesn't work, use screen recording:

1. **macOS:** Cmd+Shift+5 → Record selection
2. **Record the terminal** running the demo script
3. **Convert to GIF:**
   ```bash
   ffmpeg -i screen-recording.mov -vf "fps=10,scale=800:-1:flags=lanczos" -loop 0 assets/demo.gif
   ```

## Expected Output

Your final `assets/demo.gif` should:
- Be 2-5 MB in size
- Show ~45-60 seconds of demo
- Display at 100×30 terminal size
- Include all key commands (init, new, list, validate, stats)
- Be readable on GitHub (high contrast)
- Loop automatically

## Need Help?

If recording fails or GIF is too large, just share the raw `.cast` file and I can help optimize it.
