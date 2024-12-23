# Kobo Composite Markup Generator

## Overview

The **Kobo Composite Markup Generator** is a Python script designed to help Kobo Libre Color 2 users export and manage their markups more efficiently. Since Kobo does not provide a straightforward solution for exporting markups, this script offers a custom approach by processing your markup files and generating composite images that overlay annotations on your original book pages.

## Features

- **Automated Processing**: Iterates through all markup files (`.jpg` and `.svg`) in the `.kobo/markups` directory.
- **SVG to PNG Conversion**: Converts SVG markup files to PNG format using `cairosvg`.
- **Image Overlay**: Overlays the converted PNGs onto the original JPG pages using `Pillow`.
- **Organized Output**: Saves the resulting composite images in a structured `composite markups` directory, organized by book titles.
- **Files Associated with Chapter/Section**: Corresponding book chapter/section names are included in the naming of each composite image filename.

## Prerequisites

- **Kobo Libre Color 2**: This script was ran on a Kobo Libre Color 2 Device.
- **Anaconda or Miniconda**: Required for managing the Python environment.
- **Python 3.13.1**: The script was developed and tested with Python version 3.13.1.

## Setup Instructions

### 1. Install Anaconda or Miniconda

If you don't have Anaconda or Miniconda installed, download and install it from the following links:

- [Anaconda](https://www.anaconda.com/products/distribution)
- [Miniconda](https://docs.conda.io/en/latest/miniconda.html)

### 2. Create a Conda Environment

Open your terminal or command prompt and execute the following commands to create and activate a new Conda environment with Python 3.13.1:

```bash
conda create -n kobo-markup-env python=3.13.1
conda activate kobo-markup-env
conda install pip
```

### 3. Install Required Python Libraries

With the environment activated, install the necessary Python libraries using `pip`:

```bash
pip install pillow cairosvg
```

### 4. Download the Script

Save the provided Python script to your local machine. You can create a new file named `composite_markup_generator.py` and paste the script content into it.

### 5. Locate the Kobo Markups Directory

Ensure you know the path to your Kobo device's `markups` directory. It is typically located at:

```
.kobo/markups/
```

This directory is where your markup files (`.jpg` and `.svg`) are stored.

### 6. Place the Script in the Markups Directory

Move the `composite_markup_generator.py` script into the `.kobo/markups/` directory. The final path should look like:

```
.kobo/markups/composite_markup_generator.py
```

### 7. Execute the Script

With the Conda environment activated and the script in place, navigate to the `markups` directory and run the script:

```bash
cd ~/.kobo/markups/
python composite_markup_generator.py
```

*Note: Replace `~/.kobo/markups/` with the actual path to your `markups` directory if it's different.*

### 8. Review the Output

After execution, a new directory named `composite markups` will be created within the `markups` directory. Inside, you'll find subdirectories organized by book titles containing the composite images (`.png`) of your markups overlaid on the original pages.

## Disclaimer

Use at Your Own Risk: The Kobo Composite Markup Generator is provided "as is" without any warranties, express or implied. The author is not responsible for any damages or data loss resulting from the use of this script. Users should ensure they have backups of their data before executing the script. Always verify that the script functions correctly in a controlled environment before applying it to critical data.

## Assumptions

- **Script Location**: The script must reside in the `.kobo/markups/` directory to function correctly.
- **File Naming**: Each markup consists of a `.jpg` file of the page and an identically named `.svg` file.
- **Python Environment**: A Conda virtual environment is used, with `cairosvg` and `Pillow` libraries installed.

## Troubleshooting

- **Missing Dependencies**: Ensure that `cairosvg` and `Pillow` are installed in your Conda environment.
- **Incorrect Directory**: Verify that the script is placed in the correct `.kobo/markups/` directory.
- **Permission Issues**: On Unix-based systems, ensure the script has execute permissions.
- **Unsupported File Names**: Ensure that your markup files follow the naming convention (`basename.jpg` and `basename.svg`).

## Future Enhancements

As of December 23, 2024, this project is a work in progress. Future updates may include:

- **Standalone Executable**: A user-friendly executable version with a simple GUI.
- **Calibre Plugin**: Integration with Calibre for enhanced functionality and ease of use.

Contributions and suggestions are welcome to help improve this tool!

## Contact

For any questions, issues, or contributions, please contact [me](mailto:lauryn.eldridge3@gmail.com). Or better, go to the **Discussions** tab of this repositiory and create a new entry under the appropriate cateogry there.

---

*Thank you for using the Kobo Composite Markup Generator!*
