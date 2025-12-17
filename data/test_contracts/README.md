# Test Contract Images

This directory contains test contract pairs for validating the contract comparison agent.

## Contract Pairs

### Pair 1: Software Development Services Agreement
- **Original Contract**: `pair1_original.png`
- **Amended Contract**: `pair1_amendment.png`
- **Changes Introduced**:
  - **Section 2.2**: Added new feature "Mobile application interface"
  - **Section 2.3**: Extended delivery deadline from June 30, 2024 to August 15, 2024
  - **Section 3.1**: Increased total fee from $150,000 to $180,000
  - **Section 3.2**: Changed payment structure from 3 to 4 installments with new amounts
  - **Section 3.3**: Extended payment terms from 30 days to 45 days
  - **Section 6.3**: Extended confidentiality period from 3 years to 5 years
  - **Section 7.1**: Extended termination notice from 30 days to 60 days
  - **Section 8.4**: Added new clause regarding data breach liability cap of $500,000

### Pair 2: Consulting Services Agreement
- **Original Contract**: `pair2_original.png`
- **Amended Contract**: `pair2_amendment.png`
- **Changes Introduced**:
  - **Article I.3**: Extended engagement period from 12 months to 18 months
  - **Article II.1**: Added new service "Digital transformation consulting"
  - **Article II.2**: Increased weekly hours from 20 to 30 hours
  - **Article II.3**: Reduced delivery time from 5 business days to 3 business days
  - **Article III.1**: Increased monthly retainer from $25,000 to $35,000
  - **Article III.4**: Added monthly expense cap of $2,000
  - **Article V.4**: Extended confidentiality period from 2 years to 3 years
  - **Article VII.1**: Extended termination notice from 30 days to 45 days
  - **Article VII.3**: Added requirement to return property within 10 business days
  - **Article IX.4**: Added requirement for professional liability insurance of $2,000,000

## Image Requirements

- Format: JPEG or PNG
- Typical size: 5-10 pages per document
- Quality: Realistic scanned documents with varying quality
- Content: Legal contract documents with clear sections and amendments

## Usage

These test images can be used to validate the contract comparison agent:

```bash
python src/main.py data/test_contracts/pair1_original.png data/test_contracts/pair1_amendment.png
```

## Image Files

✅ **Image files have been generated!** The contract documents are available as PNG images:
- `pair1_original.png` - Original software development contract
- `pair1_amendment.png` - Amended software development contract
- `pair2_original.png` - Original consulting services contract
- `pair2_amendment.png` - Amended consulting services contract

These images are ready to use with the application. If you need to regenerate them, use the conversion script below.

## Regenerating Images (Optional)

If you need to regenerate the images from the text files, you can use the provided conversion script:

### Using the Conversion Script

The easiest way is to use the provided `convert_to_images.py` script:

```bash
cd data/test_contracts
python convert_to_images.py
```

This will regenerate all PNG images from the text files.

### Alternative Methods

If you prefer other methods:
```python
from PIL import Image, ImageDraw, ImageFont
import textwrap

def text_to_image(text_file, output_image, width=800, line_height=30):
    with open(text_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Create image with white background
    img = Image.new('RGB', (width, 2000), color='white')
    draw = ImageDraw.Draw(img)
    
    # Use default font or specify a font file
    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except:
        font = ImageFont.load_default()
    
    # Wrap text and draw
    y = 20
    for line in text.split('\n'):
        wrapped = textwrap.wrap(line, width=90)
        for wrap_line in wrapped:
            draw.text((20, y), wrap_line, fill='black', font=font)
            y += line_height
    
    # Crop to content
    img = img.crop((0, 0, width, min(y + 20, 2000)))
    img.save(output_image)

# Convert contracts
text_to_image('pair1_original.txt', 'pair1_original.png')
text_to_image('pair1_amendment.txt', 'pair1_amendment.png')
text_to_image('pair2_original.txt', 'pair2_original.png')
text_to_image('pair2_amendment.txt', 'pair2_amendment.png')
```

#### Method 1: Using Online Tools
1. Copy the text content from the `.txt` files
2. Use an online text-to-image converter like:
   - https://www.text2image.com
   - https://convertio.co/txt-png/
   - Or paste into Word/Google Docs and export as PDF, then convert PDF to image

#### Method 2: Using Print to PDF then Convert
1. Open the `.txt` file in a text editor
2. Print to PDF (File > Print > Save as PDF)
3. Convert PDF to PNG/JPEG using tools like:
   - Adobe Acrobat
   - Online PDF to Image converters
   - Python libraries like `pdf2image`

#### Method 3: Using Microsoft Word/Google Docs
1. Open the `.txt` file in Word or Google Docs
2. Format it as a document
3. Export/Save as PDF
4. Convert PDF to image format

## Testing

Once you have the image files, test the application:

```bash
# Test Pair 1
python src/main.py data/test_contracts/pair1_original.png data/test_contracts/pair1_amendment.png

# Test Pair 2
python src/main.py data/test_contracts/pair2_original.png data/test_contracts/pair2_amendment.png
```
