# Quick Start Guide

## Prerequisites

- **Python 3.10 or higher** (required for MCP/ADK dependencies)
- Bash shell (macOS/Linux) or Git Bash (Windows)

## Step 1: Setup Virtual Environment

### macOS/Linux

Run the setup script to create a virtual environment and install dependencies:

```bash
./setup.sh
```

**On Windows (Git Bash):**
```bash
bash setup.sh
```

### Windows (Command Prompt/PowerShell)

Run the batch file:

```cmd
setup.bat
```

This will:
- Check Python installation
- Create a virtual environment (`venv/`)
- Install all required dependencies

## Step 2: Set API Key

Get your API key from [Google AI Studio](https://aistudio.google.com/app/apikey).

### Option 1: Using .env File (Recommended)

Create a `.env` file in the project root:

```bash
# Create .env file
echo "GOOGLE_API_KEY=your_api_key_here" > .env
```

Or manually create `.env` with:
```
GOOGLE_API_KEY=your_api_key_here
```

**Note:** The `.env` file is already in `.gitignore` so it won't be committed to git.

### Option 2: Environment Variable

**macOS/Linux:**
```bash
export GOOGLE_API_KEY=your_api_key_here
```

**Windows (Command Prompt):**
```cmd
setx GOOGLE_API_KEY "your_api_key_here"
```

**Windows (PowerShell):**
```powershell
$env:GOOGLE_API_KEY="your_api_key_here"
```

Or add it to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.) to make it permanent:
```bash
echo 'export GOOGLE_API_KEY=your_api_key_here' >> ~/.zshrc
source ~/.zshrc
```

## Step 3: Run the Application

### macOS/Linux

**Web Application (Recommended):**
```bash
./run.sh
```

Or explicitly:
```bash
./run.sh web
```

Then open your browser to: **http://localhost:5000**

**CLI Application:**
```bash
./run.sh cli                    # Interactive mode
./run.sh cli "I want to plan a trip to Paris"  # Single query
```

### Windows

**Web Application (Recommended):**
```cmd
run.bat
```

Or explicitly:
```cmd
run.bat web
```

Then open your browser to: **http://localhost:5000**

**CLI Application:**
```cmd
run.bat cli                     # Interactive mode
run.bat cli "I want to plan a trip to Paris"  # Single query
```

## Manual Setup (Alternative)

If you prefer to set up manually:

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Set API key
export GOOGLE_API_KEY=your_api_key_here

# Run application
python app.py  # Web app
# or
python main.py  # CLI
```

## Troubleshooting

### Virtual Environment Issues

**If you get "MCP requires Python 3.10 or above" error:**

This means your virtual environment was created with an older Python version. The setup script will automatically detect and fix this, but you can also manually recreate the venv:

**macOS/Linux:**
```bash
./recreate_venv.sh
```

**Windows:**
```cmd
recreate_venv.bat
```

**Or manually:**
```bash
# Remove old venv
rm -rf venv

# Recreate with correct Python version
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**If setup.sh fails:**
```bash
# Make sure script is executable
chmod +x setup.sh

# Or run manually
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### API Key Issues

**If you get API key errors:**
1. Verify your key is set: `echo $GOOGLE_API_KEY`
2. Make sure you're in the activated virtual environment
3. The app will prompt you if the key is missing

### Port Already in Use

**The app automatically handles this!** If port 5000 is already in use, the application will automatically find and use the next available port (5001, 5002, etc.).

**To manually free port 5000 (macOS/Linux):**
```bash
# Find and kill the process
lsof -ti:5000 | xargs kill -9

# Or use a specific port
export FLASK_PORT=8080
./run.sh
```

**To manually free port 5000 (Windows):**
```cmd
REM Find the process
netstat -ano | findstr :5000

REM Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F

REM Or use a specific port
set FLASK_PORT=8080
run.bat
```

### Permission Denied

**If you get permission errors:**
```bash
chmod +x setup.sh run.sh
```

## Project Structure

```
Trip Planner/
├── setup.sh          # Setup script (macOS/Linux)
├── setup.bat         # Setup script (Windows)
├── run.sh            # Run script (macOS/Linux)
├── run.bat           # Run script (Windows)
├── app.py            # Web application
├── main.py           # CLI application
├── requirements.txt  # Dependencies
└── venv/             # Virtual environment (created by setup scripts)
```

## Next Steps

1. Run `./setup.sh` to set up the environment
2. Set your `GOOGLE_API_KEY`
3. Run `./run.sh` to start the web app
4. Try the sample queries in the web interface
5. Plan your trip!

For more information, see:
- [README.md](README.md) - Full documentation

---

**Happy Trip Planning!**

