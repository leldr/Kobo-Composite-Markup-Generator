#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import re
import collections
import sqlite3
import cairosvg
from PIL import Image
import io

from PyQt5.QtCore import (
    QThread, pyqtSignal, QDir, QObject
)
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QFileDialog, QHBoxLayout, QVBoxLayout, QDialog,
    QProgressBar, QTextEdit, QMessageBox
)

###############################################################################
# Real-time Print Capture
###############################################################################
class EmittingStream(QObject):
    """
    A custom stream that sends console text as a Qt signal (line by line).
    """
    textWritten = pyqtSignal(str)

    def write(self, text):
        # Each print statement often ends with '\n', but might not.
        # We'll simply emit whatever text we get.
        if text:
            self.textWritten.emit(text)

    def flush(self):
        """Required for Python 3, but can be a no-op."""
        pass


###############################################################################
# Validation Helpers
###############################################################################
def check_db_file(file_path):
    """Check that the user-provided file path is named KoboReader.sqlite and exists."""
    if not file_path or not file_path.lower().endswith("koboreader.sqlite"):
        raise ValueError("Selected file is not KoboReader.sqlite or the path is empty.")
    if not os.path.isfile(file_path):
        raise ValueError(f"Selected file '{file_path}' does not exist.")


def check_input_dir(dir_path):
    """
    Check that the user-provided input directory exists
    and that '.kobo/markups' is in its path.
    """
    if not dir_path or not os.path.isdir(dir_path):
        raise ValueError(f"Input directory '{dir_path}' does not exist.")
    # Normalize slashes to handle both Windows/macOS/Linux
    normalized = dir_path.replace("\\", "/")
    if "/markups" not in normalized:
        raise ValueError("Input directory path must contain '.kobo/markups'.")


###############################################################################
# DB Access Functions
###############################################################################
def get_volume_id_for_bookmark(bookmark_id, db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT VolumeID FROM Bookmark WHERE BookmarkID = ?", (bookmark_id,))
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if row:
        return row[0]
    return None


def get_section_title_for_bookmark(bookmark_id, db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    query = """
        SELECT Title 
        FROM content 
        WHERE ContentID = (
            SELECT ContentID 
            FROM Bookmark 
            WHERE BookmarkID = ?
        )
    """
    cursor.execute(query, (bookmark_id,))
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if row:
        return row[0]
    return None


def get_book_part_number_for_bookmark(bookmark_id, db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    query = """
        SELECT adobe_location
        FROM content 
        WHERE ContentID = (
            SELECT ContentID 
            FROM Bookmark 
            WHERE BookmarkID = ?
        )
    """
    cursor.execute(query, (bookmark_id,))
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if row:
        unclean_part_name = str(row[0]).split("/")
        part_name_with_html = unclean_part_name[-1].split(".")
        return part_name_with_html[0]
    return None


def get_ordering_number_for_bookmark(bookmark_id, db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    query = """
        SELECT StartContainerPath 
        FROM Bookmark 
        WHERE BookmarkID = ?
    """
    cursor.execute(query, (bookmark_id,))
    row = cursor.fetchone()
    
    if row:
        pattern = re.compile(r'point\((/[\d/]+:\d+)\)')
        match = pattern.search(row[0])
        if match:
            extracted_point_location = match.group(1)
            cleaned_point_location = extracted_point_location.replace(":", ".").replace("/", ".")
            cursor.close()
            conn.close()
            return cleaned_point_location

    cursor.close()
    conn.close()
    return None


###############################################################################
# SVG + JPG -> PNG Composite
###############################################################################
def overlay_svg_on_jpg(
    jpg_path, 
    svg_path, 
    output_path,
    final_width=1264, 
    final_height=1680
):
    temp_overlay = "temp_overlay.png"

    print(f"Overlaying:\n  JPG: {jpg_path}\n  SVG: {svg_path}\n-> {output_path}")

    try:
        # Convert SVG -> PNG
        cairosvg.svg2png(
            url=svg_path,
            write_to=temp_overlay,
            output_width=final_width,
            output_height=final_height
        )

        # Resize the JPG
        bg_image = Image.open(jpg_path).convert("RGBA")
        bg_image = bg_image.resize(
            (final_width, final_height),
            Image.Resampling.LANCZOS
        )

        # Open the rendered PNG
        overlay_image = Image.open(temp_overlay).convert("RGBA")

        # Composite
        composite_image = Image.alpha_composite(bg_image, overlay_image)

        # Save
        composite_image.save(output_path, format="PNG")
        print(f"Saved composite image: {output_path}\n")

    except Exception as e:
        print(f"Could not process {svg_path} with {jpg_path}: {e}\n")

    finally:
        if os.path.exists(temp_overlay):
            os.remove(temp_overlay)


###############################################################################
# Main Script Logic
###############################################################################
def main(db_path, input_dir, output_dir, progress_callback=None):
    """
    1) Creates a subfolder "composite markups" in the user-chosen output_dir.
    2) Finds all .jpg + .svg pairs in the user-chosen input_dir that share the same base name.
    3) Overlays the SVG on top of the JPG at 1264 x 1680.
    4) Saves the resulting PNG in output_dir/composite markups/<book_title>.
    5) Calls progress_callback(i, total) after each processed pair, if provided.
    """

    print("Starting main script logic...")
    print(f"DB Path: {db_path}")
    print(f"Input Dir: {input_dir}")
    print(f"Output Dir: {output_dir}\n")

    base_output_dir = os.path.join(output_dir, "composite markups")
    os.makedirs(base_output_dir, exist_ok=True)
    print(f"Created/verified base output dir: {base_output_dir}\n")

    all_files = os.listdir(input_dir)
    file_map = collections.defaultdict(list)

    # Identify .jpg and .svg pairs
    for filename in all_files:
        base, ext = os.path.splitext(filename)
        ext = ext.lower()
        if ext in (".jpg", ".svg"):
            file_map[base].append(ext)
            # If ext is SVG, attempt to get book title
            if ext == ".svg":
                unclean_vol_id = get_volume_id_for_bookmark(base, db_path)
                if unclean_vol_id is None:
                    book_title = "UnknownBook"
                else:
                    vol_split = unclean_vol_id.split("/")
                    book_title = vol_split[-1] if vol_split else "UnknownBook"
                file_map[base].append(book_title)

    # Count how many pairs exist (for progress updates)
    pairs_to_process = [
        base for base, exts in file_map.items()
        if ".jpg" in exts and ".svg" in exts
    ]
    total_pairs = len(pairs_to_process)

    if total_pairs == 0:
        print("No matching .jpg + .svg pairs found.\n")
        return

    print(f"Found {total_pairs} matching pairs. Beginning overlay...\n")

    processed_count = 0
    for base_name in pairs_to_process:
        processed_count += 1

        # Possibly multiple appended book_title strings in exts
        exts = file_map[base_name]
        possible_titles = [x for x in exts if x not in (".jpg", ".svg")]
        book_title = possible_titles[-1] if possible_titles else "UnknownBook"

        jpg_path = os.path.join(input_dir, base_name + ".jpg")
        svg_path = os.path.join(input_dir, base_name + ".svg")

        bookmark_section_name = get_section_title_for_bookmark(base_name, db_path)
        if not bookmark_section_name or len(str(bookmark_section_name)) <= 1:
            bookmark_section_name = f"Chapter {bookmark_section_name}"

        book_part_name = get_book_part_number_for_bookmark(base_name, db_path)
        markup_exact_location = get_ordering_number_for_bookmark(base_name, db_path)

        # Construct a final filename
        output_name = (
            f"markup_{bookmark_section_name}_"
            f"{book_part_name}{markup_exact_location}_"
            f"{base_name[:8]}.png"
        )

        # Each book gets its own folder
        book_dir = os.path.join(base_output_dir, book_title)
        os.makedirs(book_dir, exist_ok=True)

        output_path = os.path.join(book_dir, output_name)
        overlay_svg_on_jpg(jpg_path, svg_path, output_path)

        # Update progress bar in real time
        if progress_callback:
            progress_callback(processed_count, total_pairs)

    print("\nAll matching .jpg + .svg pairs have been processed.")
    print(f"Processed {processed_count} pairs.\n")


###############################################################################
# Worker Thread
###############################################################################
class CompositeScriptThread(QThread):
    """
    Runs the `main(db_path, input_dir, output_dir, ...)` in a background thread,
    capturing prints line-by-line so we can update the GUI console in real time.
    """
    line_signal = pyqtSignal(str)         # Emitted each time a line is printed
    progress_signal = pyqtSignal(int, int)  # (current, total)
    finished_signal = pyqtSignal(str)     # final text (buffer) once done

    def __init__(self, db_path, input_dir, output_dir, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.input_dir = input_dir
        self.output_dir = output_dir

        # We'll store all console text in a buffer so we can emit it at the end as well.
        self._buffer = []

    def run(self):
        # Create EmittingStream to capture all prints line-by-line
        emitting_stream = EmittingStream()
        emitting_stream.textWritten.connect(self.on_new_stdout_line)

        # Save old stdout/stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = emitting_stream
        sys.stderr = emitting_stream

        try:
            def progress_callback(current, total):
                self.progress_signal.emit(current, total)

            main(
                self.db_path,
                self.input_dir,
                self.output_dir,
                progress_callback=progress_callback
            )

        except Exception as e:
            print(f"Error running script: {e}")

        finally:
            # Restore old stdout/stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            # Emit everything collected in _buffer as final output
            final_output = "".join(self._buffer)
            self.finished_signal.emit(final_output)

    def on_new_stdout_line(self, text):
        """
        Called each time the script prints a line.
        We'll both store it and emit a line_signal
        so the GUI can update in real time.
        """
        self._buffer.append(text)
        self.line_signal.emit(text)


###############################################################################
# Progress/Console Window
###############################################################################
class ProgressWindow(QDialog):
    """
    Shows:
      1) A progress bar (0%..100%)
      2) A live console area
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Running Composite Script...")
        self.resize(600, 350)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 1)  # We'll set real range once we know total
        self.progress_bar.setValue(0)

        self.console_text = QTextEdit()
        self.console_text.setReadOnly(True)

        layout = QVBoxLayout()
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.console_text)
        self.setLayout(layout)

    def set_progress_range(self, total):
        self.progress_bar.setRange(0, total)

    def update_progress(self, current):
        self.progress_bar.setValue(current)

    def append_text(self, text):
        self.console_text.insertPlainText(text)
        self.console_text.ensureCursorVisible()


###############################################################################
# Main GUI
###############################################################################
class SimpleGui(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Composite Markup Generator Tool")

        # Create labels
        self.file_label = QLabel("KoboReader.sqlite File:")
        self.input_label = QLabel("Input Directory (.kobo/markups):")
        self.output_label = QLabel("Output Directory:")

        # Create line edits
        self.file_line_edit = QLineEdit()
        self.input_line_edit = QLineEdit()
        self.output_line_edit = QLineEdit()

        # Create buttons
        self.file_button = QPushButton("Browse...")
        self.file_button.clicked.connect(self.browse_file)

        self.input_button = QPushButton("Browse...")
        self.input_button.clicked.connect(self.browse_input_directory)

        self.output_button = QPushButton("Browse...")
        self.output_button.clicked.connect(self.browse_output_directory)

        # Run script button
        self.run_button = QPushButton("Run Composite Markups")
        self.run_button.clicked.connect(self.run_composite_script)

        # Layout for selecting file
        file_layout = QHBoxLayout()
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(self.file_line_edit)
        file_layout.addWidget(self.file_button)

        # Layout for selecting input directory
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.input_label)
        input_layout.addWidget(self.input_line_edit)
        input_layout.addWidget(self.input_button)

        # Layout for selecting output directory
        output_layout = QHBoxLayout()
        output_layout.addWidget(self.output_label)
        output_layout.addWidget(self.output_line_edit)
        output_layout.addWidget(self.output_button)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(file_layout)
        main_layout.addLayout(input_layout)
        main_layout.addLayout(output_layout)
        main_layout.addWidget(self.run_button)
        self.setLayout(main_layout)

    def browse_file(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select KoboReader.sqlite",
            QDir.homePath(),
            "SQLite Database Files (KoboReader.sqlite)",
            options=options
        )
        if file_path:
            self.file_line_edit.setText(file_path)

    def browse_input_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Input Directory",
            ""
        )
        if directory:
            self.input_line_edit.setText(directory)

    def browse_output_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            ""
        )
        if directory:
            self.output_line_edit.setText(directory)

    def run_composite_script(self):
        db_file = self.file_line_edit.text()
        input_dir = self.input_line_edit.text()
        output_dir = self.output_line_edit.text()

        # Validate
        try:
            check_db_file(db_file)
            check_input_dir(input_dir)
            if not output_dir:
                raise ValueError("Output directory path is empty.")
            if not os.path.isdir(output_dir):
                raise ValueError(f"Output directory '{output_dir}' does not exist.")
        except ValueError as e:
            QMessageBox.critical(self, "Error", str(e))
            return

        # Show progress window
        self.progress_window = ProgressWindow(self)
        self.progress_window.show()

        # Create the background thread
        self.thread = CompositeScriptThread(db_file, input_dir, output_dir)

        # Connect signals:
        # 1) line_signal => append text as soon as it's printed
        self.thread.line_signal.connect(self.progress_window.append_text)

        # 2) progress_signal => update progress bar
        self.thread.progress_signal.connect(self.on_progress_update)

        # 3) finished_signal => final text or "Done!"
        self.thread.finished_signal.connect(self.on_script_finished)

        # Start
        self.thread.start()

    def on_progress_update(self, current, total):
        """
        Update the progress bar. If it's the first time, set the range properly.
        """
        if self.progress_window.progress_bar.maximum() == 1 and total > 1:
            self.progress_window.set_progress_range(total)
        self.progress_window.update_progress(current)

    def on_script_finished(self, final_output):
        """
        Called when the script finishes. 
        We'll append the final buffer, then print "Done!"
        """
        self.progress_window.append_text("""\nDone!\n\nClose out of this pop-up to return to the main dialog window. If you're completely done with this tool, please close the main dialog window as well.\n\nThank you for using the Composite Markup Generator Tool!\n\nTool Creator: Lauryn Eldridge (@leldr on github)\n
                                         """)


###############################################################################
# Entry Point
###############################################################################
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SimpleGui()
    window.show()
    sys.exit(app.exec_())
