# Radio Programming Files

This repository contains programming files for various radio devices and a custom parser for converting binary `.img` files to CSV format.

## Files

### Radio Programming Files (.img)
- `AR-5RM.img` - AR-5RM radio programming
- `Baofeng_BF-F8HP_20260215.img` - Baofeng BF-F8HP programming
- `mike-bf-f8+.img` - Baofeng BF-F8+ programming

### CSV Exports
Human-readable CSV exports of the radio programming files are available in the `csv/` directory for easy viewing and version control diffing.

## Tools

### parse_baofeng.py

A custom Python script that parses binary `.img` files and exports channel data to CSV format.

**Usage:**

```bash
# Convert a single file
python3 parse_baofeng.py <img_file> [output.csv]

# Convert all .img files in the current directory
python3 parse_baofeng.py --all
```

**Features:**
- Decodes BCD-encoded frequencies
- Extracts RX/TX frequencies, power levels, and tone data
- Supports multiple radio formats (AR-5RM, Baofeng, etc.)
- Exports to CSV for easy viewing and version control

**Output format:**
- Channel number
- Channel name (if available)
- RX frequency (MHz)
- TX frequency (MHz)
- Power level
- Tone/CTCSS codes

## Requirements

- Python 3.x (standard library only, no external dependencies)

## Notes

The `.img` files are binary radio programming files typically created with CHIRP or manufacturer-specific software. The CSV exports make it easier to track changes and review channel configurations without needing specialized radio programming software.
