import math

import rasterio
import tifffile
from typing import List
import pdb
from PIL import Image
import io
import matplotlib.pyplot as plt


def tile2latlon(x, y, z):
    # Calculate the total number of tiles at the given zoom level (2^z)
    n = 2.0**z

    # Convert tile x coordinate to longitude
    lon_deg = (
        x / n * 360.0 - 180.0
    )  # scale x coordinate, convert to degrees, align to -180 to +180

    # Convert tile y coordinate to latitude
    lat_rad = math.atan(
        math.sinh(math.pi * (1 - 2 * y / n))
    )  # transform y coordinate, convert to radians
    lat_deg = math.degrees(lat_rad)  # convert latitude from radians to degrees

    # Return the calculated latitude and longitude
    return (lat_deg, lon_deg)


def latlon2tile(latitude, longitude, zoom):
    """
    Converts geographic coordinates (latitude, longitude) to tile coordinates (x, y) at a specified zoom level.

    Parameters:
        latitude (float): The latitude in decimal degrees.
        longitude (float): The longitude in decimal degrees.
        zoom (int): The zoom level.

    Returns:
        tuple: Returns the (x, y) tile coordinates as integers.
    """

    # Convert latitude to radians
    lat_rad = math.radians(latitude)

    # Calculate the total number of tiles at the given zoom level (2^zoom)
    num_tiles = 2.0**zoom

    # Calculate the x tile coordinate based on longitude
    x_tile = int((longitude + 180.0) / 360.0 * num_tiles)

    # Calculate the y tile coordinate based on latitude
    y_tile = int(
        (1.0 - math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi)
        / 2.0
        * num_tiles
    )

    return x_tile, y_tile


def get_tile_byte_ranges(tiff_path, tile_indices, page_number):
    """
    Read TIFF tile byte ranges from a TIFF file.

    Parameters:
    - tiff_path: Path to the TIFF file.
    - tile_indices: A list of tile indices for which to fetch byte ranges.
    - page_number: Page number to read from.

    Returns:
    - Dictionary of tile indices to their byte ranges (offset, length).
    """
    byte_ranges = {}
    with tifffile.TiffFile(tiff_path) as tif:
        page = tif.pages[page_number]
        if not page.is_tiled:
            raise ValueError("Selected page is not tiled.")
        tile_offsets = page.tags["TileOffsets"].value
        tile_byte_counts = page.tags["TileByteCounts"].value

        for index in tile_indices:
            if index < len(tile_offsets) and index < len(tile_byte_counts):
                offset = tile_offsets[index]
                length = tile_byte_counts[index]
                byte_ranges[index] = (offset, offset + length - 1)

    return byte_ranges


def find_page_number_for_overview(tiff_path, desired_scale):
    """
    Find the page number in a TIFF file that corresponds to a given desired overview scale.

    Parameters:
    - tiff_path: Path to the TIFF file.
    - desired_scale: The desired overview scale (e.g., 2, 4, 8, 16, 32).

    Returns:
    - int: Page number of the TIFF file that corresponds to the desired overview scale.
    """
    with tifffile.TiffFile(tiff_path) as tif:
        full_res_width = tif.pages[0].imagewidth
        for i, page in enumerate(tif.pages):
            # Checks if the page is tiled.
            if "TileWidth" in page.tags:
                # Calculate the scale based on page width.
                current_scale = math.ceil(full_res_width / page.imagewidth)
                if current_scale == desired_scale:
                    return i
    return None


def calculate_tile_range():
    cog_path = "./begunia_ortho_cog.tif"
    zoom_level = 21
    tile_x = 1555498
    tile_y = 905671
    tile_size = 256

    with rasterio.open(cog_path) as src:
        closest_overview = min(src.overviews(1), key=lambda x: abs(x - zoom_level))
        page_number = find_page_number_for_overview(cog_path, closest_overview)

        with tifffile.TiffFile(cog_path) as tif:
            overview_factor = 2**closest_overview

            pixel_x = (tile_x * tile_size) // overview_factor
            pixel_y = (tile_y * tile_size) // overview_factor

            # Determine the tile index within the overview level
            tiles_across = src.width // (tile_size * overview_factor)
            tile_index = (pixel_y // tile_size) * tiles_across + (pixel_x // tile_size)

        byte_ranges = get_tile_byte_ranges(cog_path, [tile_index], page_number)

        byte_range = byte_ranges[tile_index]
        print(f"Byte Ranges for the requested tile: {byte_ranges}")
        with open(cog_path, "rb") as file:
            file.seek(byte_range[0])  # Move to the start of the tile data

            tile_data = file.read(
                byte_range[1] - byte_range[0] + 1
            )  # Read the specified byte range

            image_stream = io.BytesIO(tile_data)
            image = Image.open(image_stream)
            image = image.convert("RGB")  # Ensure it's in RGB format
            plt.imshow(image)
            plt.show()


if __name__ == "__main__":
    calculate_tile_range()
