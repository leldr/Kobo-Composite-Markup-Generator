#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import collections
import cairosvg
from PIL import Image
import sqlite3
from svgpathtools import svg2paths
from cairosvg import svg2png
import io


def compute_path_bbox(svg_path):
    """
    Compute the bounding box of all <path> elements in the SVG using svgpathtools.
    Returns (xmin, ymin, xmax, ymax).
    Raises ValueError if no valid path geometry is found.
    """
    paths, _ = svg2paths(svg_path)
    if not paths:
        raise ValueError("No <path> elements found or no valid geometry in the SVG.")

    # Initialize bounding box to extremes
    min_x = float("inf")
    max_x = float("-inf")
    min_y = float("inf")
    max_y = float("-inf")

    # Accumulate bounding box for each path
    for path in paths:
        # bbox() returns (xmin, xmax, ymin, ymax)
        xmin, xmax, ymin, ymax = path.bbox()
        min_x = min(min_x, xmin)
        max_x = max(max_x, xmax)
        min_y = min(min_y, ymin)
        max_y = max(max_y, ymax)

    if min_x == float("inf") or min_y == float("inf"):
        raise ValueError("Unable to compute bounding box from <path> data.")
    padding = 50
    min_x -= padding
    max_x += padding
    min_y -= padding
    max_y += padding
    return (min_x, min_y, max_x, max_y)


def crop_jpeg(jpeg_path, cropped_jpeg_path, bbox):
    """
    Crop the JPEG image at `jpeg_path` to `bbox` (xmin, ymin, xmax, ymax),
    then save it to `cropped_jpeg_path`.
    """
    img = Image.open(jpeg_path)
    left, upper, right, lower = bbox
    cropped_img = img.crop((left, upper, right, lower))
    cropped_img.save(cropped_jpeg_path, format="JPEG")
    print(f"[INFO] Cropped JPEG saved to {cropped_jpeg_path}")


def rasterize_and_crop_svg(svg_path, bbox):
    """
    Convert the entire SVG to a PNG in memory using cairosvg, then crop it
    to the same bounding box. Returns the cropped PNG as a PIL Image object.
    """
    # Read SVG into memory
    with open(svg_path, "rb") as f:
        svg_data = f.read()

    # Convert SVG to PNG (in-memory) with cairosvg
    png_data = svg2png(bytestring=svg_data)

    # Open as a Pillow Image
    full_svg_png = Image.open(io.BytesIO(png_data))

    # Crop the rasterized SVG
    left, upper, right, lower = bbox
    cropped_svg_png = full_svg_png.crop((left, upper, right, lower))

    return cropped_svg_png


def overlay_cropped_svg_on_jpeg(cropped_jpeg_path, cropped_svg_img, output_path):
    """
    Overlays the PIL Image `cropped_svg_img` (already cropped to bounding box)
    on top of the cropped JPEG at `cropped_jpeg_path`, then saves to `output_path`.
    """
    base_img = Image.open(cropped_jpeg_path).convert("RGBA")
    overlay_img = cropped_svg_img.convert("RGBA")

    # Paste overlay onto base (with alpha)
    base_img.paste(overlay_img, (0, 0), overlay_img)

    # Optionally convert back to RGB if you want a JPEG output (no alpha)
    final = base_img.convert("RGB")
    final.save(output_path, format="JPEG")
    print(f"[INFO] Final overlay image saved to {output_path}")

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
            cropped_temp = os.path.join(book_dir, "cropped_temp")
            # Overlay the images
            #overlay_svg_on_jpg(jpg_path, svg_path, output_path)
             # 1) Compute bounding box based on <path> in the SVG
            (xmin, ymin, xmax, ymax) = compute_path_bbox(svg_path)
            print(f"[INFO] BBox from SVG paths: (xmin={xmin}, ymin={ymin}, xmax={xmax}, ymax={ymax})")

    # 2) Crop the JPEG using that bounding box
            crop_jpeg(jpg_path, cropped_temp, (xmin, ymin, xmax, ymax))

    # 3) Rasterize the SVG to PNG, then crop that PNG
            cropped_svg_image = rasterize_and_crop_svg(svg_path, (xmin, ymin, xmax, ymax))

    # 4) Overlay the cropped SVG onto the newly cropped JPEG
            overlay_cropped_svg_on_jpeg(cropped_temp, cropped_svg_image, output_path)

    print("All matching .jpg + .svg pairs have been processed.")

if __name__ == "__main__":
    main()
