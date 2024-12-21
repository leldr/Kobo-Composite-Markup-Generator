#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import collections
import cairosvg
from PIL import Image
import sqlite3

def get_volume_id_for_bookmark(bookmark_id):
    """
    Retrieves the VolumeID for a given BookmarkID from the Bookmark table.
    
    :param bookmark_id: The BookmarkID (string) to look up in the database.
    :return: The VolumeID (string) if found, otherwise None.
    """
    conn = sqlite3.connect("../KoboReader.sqlite")
    cursor = conn.cursor()

    cursor.execute("SELECT VolumeID FROM Bookmark WHERE BookmarkID = ?", (bookmark_id,))
    row = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if row:
        return row[0]
    return None


def overlay_svg_on_jpg(
    jpg_path, 
    svg_path, 
    output_path,
    final_width=1264, 
    final_height=1680
):
    """
    Overlays an SVG on a JPG at a fixed size of 1264 x 1680.

    Steps:
        1) Convert SVG to PNG at 1264 x 1680 (temp file).
        2) Resize background JPG to 1264 x 1680 (if needed).
        3) Alpha-composite them (overlay on top).
        4) Save result as a PNG.
    """
    temp_overlay = "temp_overlay.png"

    try:
        # 1. Convert SVG -> PNG
        cairosvg.svg2png(
            url=svg_path,
            write_to=temp_overlay,
            output_width=final_width,
            output_height=final_height
        )

        # 2. Open the JPG, resize to match
        bg_image = Image.open(jpg_path).convert("RGBA")
        bg_image = bg_image.resize(
            (final_width, final_height),
            Image.Resampling.LANCZOS
        )

        # 3. Open the rendered PNG
        overlay_image = Image.open(temp_overlay).convert("RGBA")

        # 4. Composite
        composite_image = Image.alpha_composite(bg_image, overlay_image)

        # 5. Save
        composite_image.save(output_path, format="PNG")
        print(f"Saved composite image at: {output_path}")

    except Exception as e:
        print(f"Could not process {svg_path} with {jpg_path}: {e}")

    finally:
        # Remove temp file if it exists
        if os.path.exists(temp_overlay):
            os.remove(temp_overlay)

def main():
    """
    1) Creates a subfolder "composite markups" in the same directory as this script.
    2) Finds all .jpg + .svg pairs that share the same base name.
       Example: "mypage.jpg" + "mypage.svg" => "mypage_composite.png"
    3) Overlays the SVG on top of the JPG at 1264 x 1680.
    4) Saves the resulting PNG in "composite markups/<book_title>".
    """
    # Script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Base output directory
    base_output_dir = os.path.join(script_dir, "composite markups")
    os.makedirs(base_output_dir, exist_ok=True)

    # Gather all files in script_dir
    all_files = os.listdir(script_dir)

    # We’ll map each base name -> list of metadata
    # e.g. file_map["ABC-UUID"] = [".jpg", ".svg", "MyBookTitle"]
    file_map = collections.defaultdict(list)

    # 1) Build up the mapping
    for filename in all_files:
        full_path = os.path.join(script_dir, filename)
        if os.path.isdir(full_path):
            continue  # skip directories

        base, ext = os.path.splitext(filename)
        ext = ext.lower()

        # We only care about .jpg and .svg for pairing
        if ext in (".jpg", ".svg"):
            file_map[base].append(ext)

            # If it's an .svg, we look up the VolumeID => last part => book folder
            if ext == ".svg":
                unclean_vol_id = get_volume_id_for_bookmark(base)
                # Handle case if unclean_vol_id is None
                if unclean_vol_id is None:
                    book_title = "UnknownBook"
                else:
                    vol_split = unclean_vol_id.split("/")
                    book_title = vol_split[-1] if vol_split else "UnknownBook"
                
                file_map[base].append(book_title)

    # 2) Process only those base names that have BOTH .jpg AND .svg
    for base_name, exts in file_map.items():
        if ".jpg" in exts and ".svg" in exts:
            # exts should look like [".svg", "BookTitle"] or [".jpg", ".svg", "BookTitle"] etc.
            # So let's extract the book folder name.
            # We'll assume the last element is the book title if ext == ".svg" was found.
            # Find the element that is not .jpg or .svg
            possible_titles = [x for x in exts if x not in (".jpg", ".svg")]
            if possible_titles:
                book_title = possible_titles[-1]
            else:
                book_title = "UnknownBook"

            # Build full paths
            jpg_path = os.path.join(script_dir, base_name + ".jpg")
            svg_path = os.path.join(script_dir, base_name + ".svg")

            # Output file => "<basename>_composite.png"
            output_name = f"{base_name}_composite.png"

            # Create a subfolder inside "composite markups" for the book
            book_dir = os.path.join(base_output_dir, book_title)
            os.makedirs(book_dir, exist_ok=True)

            # Final path => "composite markups/<book_title>/<basename>_composite.png"
            output_path = os.path.join(book_dir, output_name)

            # Overlay the images
            overlay_svg_on_jpg(jpg_path, svg_path, output_path)

    print("All matching .jpg + .svg pairs have been processed.")

if __name__ == "__main__":
    main()
