# Composite Markup Generator with GUI

This README walks you through:
1. **Setting up a conda environment** and installing dependencies (`pip`, `cairosvg`, `pillow`, `pyqt5`) to run the script with a graphical user interface (GUI).  
2. **Generating a standalone executable** from the Python script using [PyInstaller](https://pyinstaller.org/en/stable/) so you can distribute/run the tool without needing Python installed.

---

## 1. Environment Setup and Running the Script

### Prerequisites
- A basic understanding of Python and the command line.
- [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda](https://www.anaconda.com/) installed on your machine.
- The script file (e.g., `composite_markup_generator_with_GUI.py`).

### Steps

#### 1. Create and Activate a Conda Environment
Open your terminal (macOS/Linux) or Anaconda Prompt (Windows), then run:
```bash
conda create -n kobo-markup-env python=3.9
conda activate kobo-markup-env
```
> **Why?** Creating a new environment helps keep your project and system dependencies isolated.

#### 2. Install Dependencies
Within your newly activated `kobo-markup-env`, install the required libraries:
```bash
conda install pip
conda install cairosvg pyqt5 pillow
```
> Alternatively, if you prefer pip for everything:
> ```bash
> pip install cairosvg pyqt5 pillow
> ```

#### 3. Run the Python Script
Once the environment is ready and you have the script (`composite_markup_generator_with_GUI.py`), you can execute it directly:
```bash
python composite_markup_generator_with_GUI.py
```
- This will launch a graphical user interface (GUI).
- Within the GUI, you can select your `KoboReader.sqlite` database, input directory, and output directory, then start the script to process markups.

---

## 2. Generating a Standalone Executable (Using PyInstaller)

If you want to **distribute** your script to others who might not have Python or your conda environment, you can create a standalone executable.

### Install PyInstaller
First, ensure you have PyInstaller installed in the same environment:
```bash
pip install pyinstaller
```
*(If you already installed it via conda, that’s fine too.)*

### Build the Executable
Navigate to the folder containing `composite_markup_generator_with_GUI.py` and run:
```bash
pyinstaller composite_markup_generator_with_GUI.py --onefile
```
> **What this does**:  
> - `--onefile` creates a single, self-contained executable in a `dist/` folder.  
> - Other options (like `--windowed` on Windows, or `--noconsole`) can change how the executable runs.

### Locate and Run the Executable
After PyInstaller finishes:
- Look for a `dist/` directory next to your script.
- Inside `dist/`, you’ll see an executable named `composite_markup_generator_with_GUI` (on macOS/Linux) or `composite_markup_generator_with_GUI.exe` (on Windows).

#### macOS/Linux
1. You may need to mark the file as executable:
   ```bash
   chmod +x dist/composite_markup_generator_with_GUI
   ```
2. Run the tool:
   ```bash
   ./dist/composite_markup_generator_with_GUI
   ```
3. If you’re on macOS and you get a security warning, you may need to right-click → Open, or go to System Preferences → Security & Privacy to allow it to run.

#### Windows
1. In Windows Explorer, navigate to the `dist\` folder.
2. Double-click `composite_markup_generator_with_GUI.exe`. 
3. If Windows Defender or SmartScreen blocks it, you may need to click “More info” → “Run anyway.”

### Running The Executable

Unlike the `composite_markup_generator.py` at the top-most directory of this repository, both the `composite_markup_generator_with_GUI.py` and the executable `composite_markup_generator_with_GUI` can be place anywhere in the current user's directory (as opposed to HAVING to place the script in the .kobo/markups directory). Simply copy and paste the executable lcoated in the `./dist/` directory to your desired location on your system. Future iterations of this tool will have readily-available distributabnle execution files for various operating systems.

---

## Troubleshooting & Tips

- **Missing DLLs or Libraries**: Sometimes PyInstaller can miss hidden imports. If your executable crashes on another machine, you might need to add `--hidden-import` flags for libraries, or try including PyInstaller’s `collect_all` hooks.  
- **Environment Differences**: Make sure the environment in which you run PyInstaller is as close as possible to what’s needed on the target machine.  
- **File Paths**: If your script loads external files or assets, ensure the code references them correctly once compiled. You may need to use PyInstaller’s mechanisms for including data files.  

---

## Additional Notes

- **Why PyInstaller?**  
  PyInstaller bundles the Python interpreter and all required modules into a single folder or file, making distribution simpler.

- **Platform-Specific Binaries**  
  If you need executables for multiple platforms (Windows, macOS, Linux), you generally must run PyInstaller on each platform to produce the compatible executables.

---

### Disclaimer
This tool is provided “as is,” without warranty of any kind. Use it at your own risk.  
**No commercial use permitted** unless explicitly agreed upon with the author.  

### Contact
For inquiries or more advanced usage scenarios, please reach out to the project’s maintainer or check the official PyInstaller documentation for in-depth guides.
