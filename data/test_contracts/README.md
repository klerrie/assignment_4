# Test Contract Images

This directory contains test contract pairs for validating the contract comparison agent.

## Contract Pairs

### Pair 1: Payment Terms Amendment
- **Original Contract**: `pair1_original.png`
- **Amended Contract**: `pair1_amendment.png`
- **Changes Introduced**:
  - Payment terms extended from 30 days to 45 days in Section 3
  - Added new clause regarding late payment penalties
  - Modified delivery schedule in Section 5

### Pair 2: Termination Clause Amendment
- **Original Contract**: `pair2_original.png`
- **Amended Contract**: `pair2_amendment.png`
- **Changes Introduced**:
  - Added new termination clause in Section 7 allowing either party to terminate with 60 days notice
  - Modified liability limitations in Section 8
  - Updated intellectual property rights section (Section 9)

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

## Note

Place your actual test contract images in this directory. The filenames should follow the pattern:
- `pair{N}_original.{ext}`
- `pair{N}_amendment.{ext}`

Where `{N}` is the pair number and `{ext}` is the image extension (jpg, png, etc.).
