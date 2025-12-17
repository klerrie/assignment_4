"""
Script to convert text contract files to PNG images for testing.
Requires: pip install Pillow
"""
from PIL import Image, ImageDraw, ImageFont
import textwrap
from pathlib import Path

def text_to_image(text_file, output_image, width=800, line_height=25, margin=40):
    """
    Convert a text file to a PNG image.
    
    Args:
        text_file: Path to input text file
        output_image: Path to output image file
        width: Image width in pixels
        line_height: Height of each line in pixels
        margin: Margin around text in pixels
    """
    # Read text file
    with open(text_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Try to use a nice font, fallback to default
    try:
        # Try common system fonts
        font_paths = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/times.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        ]
        font = None
        for font_path in font_paths:
            try:
                font = ImageFont.truetype(font_path, 12)
                break
            except:
                continue
        if font is None:
            font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()
    
    # Calculate required height
    lines = []
    for paragraph in text.split('\n'):
        if paragraph.strip():
            wrapped = textwrap.wrap(paragraph, width=90)
            lines.extend(wrapped)
        else:
            lines.append('')  # Empty line
    
    height = len(lines) * line_height + (2 * margin)
    
    # Create image with white background
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw text
    y = margin
    for line in lines:
        if line.strip():  # Only draw non-empty lines
            draw.text((margin, y), line, fill='black', font=font)
        y += line_height
    
    # Save image
    img.save(output_image, 'PNG', quality=95)
    print(f"Converted {text_file} to {output_image}")


if __name__ == "__main__":
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    
    # Convert all contract pairs
    contracts = [
        ("pair1_original.txt", "pair1_original.png"),
        ("pair1_amendment.txt", "pair1_amendment.png"),
        ("pair2_original.txt", "pair2_original.png"),
        ("pair2_amendment.txt", "pair2_amendment.png"),
    ]
    
    for text_file, image_file in contracts:
        text_path = script_dir / text_file
        image_path = script_dir / image_file
        
        if text_path.exists():
            text_to_image(str(text_path), str(image_path))
        else:
            print(f"Warning: {text_file} not found, skipping...")
