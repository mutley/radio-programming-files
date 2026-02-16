#!/usr/bin/env python3
"""
Parse Baofeng .img files and export to CSV
Based on reverse engineering the binary format
"""

import struct
import sys
import csv
import os

def bcd_to_frequency(data):
    """Convert BCD encoded frequency bytes to MHz"""
    # Baofeng stores frequencies in BCD format (4 bytes)
    # Example: 50 62 25 46 = 462.5625 MHz
    try:
        freq_str = ""
        for byte in data:
            if byte == 0xff:
                return None
            # Each byte has two digits in BCD
            high = (byte >> 4) & 0x0F
            low = byte & 0x0F
            if high > 9 or low > 9:
                return None
            freq_str += f"{high}{low}"
        
        # Convert to float MHz
        freq_mhz = float(freq_str) / 10000.0
        
        # Sanity check: typical ham/commercial radio range
        if freq_mhz < 50 or freq_mhz > 1000:
            return None
            
        return freq_mhz
    except:
        return None

def parse_channel(data, channel_num, has_name=False, skip_byte=False):
    """Parse a single channel entry"""
    min_size = 32 if has_name else 16
    if len(data) < min_size:
        return None
    
    # Some formats have a leading zero byte before frequency
    offset = 1 if skip_byte else 0
    
    # Try to extract RX frequency (4 bytes in BCD, possibly after offset)
    rx_freq = bcd_to_frequency(data[offset:offset+4])
    if not rx_freq:
        # Try without offset if it failed
        if skip_byte:
            rx_freq = bcd_to_frequency(data[0:4])
            offset = 0
        if not rx_freq:
            return None
    
    # Try to extract TX frequency (next 4 bytes in BCD)
    tx_freq = bcd_to_frequency(data[offset+4:offset+8])
    if not tx_freq:
        tx_freq = rx_freq  # Simplex if no TX specified
    
    # Extract tone/CTCSS if present (bytes 8-9)
    tone_data = data[8:10] if len(data) >= 10 else b'\x00\x00'
    
    # Extract power and other flags (byte 14 or 15 depending on format)
    flags = data[14] if len(data) >= 15 else 0x44
    
    # Determine power level (common values: 0x40=low, 0x44=high, 0x01=high)
    power = "High" if (flags & 0x04) or (flags & 0x01) else "Low"
    
    # Extract channel name if present (starts at byte 16)
    name = ""
    if has_name and len(data) >= 32:
        name_bytes = data[16:32]
        try:
            # Remove 0xff padding and decode ASCII
            name = name_bytes.split(b'\xff')[0].decode('ascii', errors='ignore').strip()
        except:
            pass
    
    result = {
        'channel': channel_num,
        'name': name,
        'rx_freq': f"{rx_freq:.4f}",
        'tx_freq': f"{tx_freq:.4f}",
        'power': power,
        'tone': ''.join(f'{b:02x}' for b in tone_data)
    }
    
    return result

def parse_baofeng_img(filename):
    """Parse a Baofeng .img file and return channel list"""
    channels = []
    
    with open(filename, 'rb') as f:
        data = f.read()
    
    # Detect format by checking if channel names are present
    # AR-5RM has names at offset 0x10 in each channel block
    has_names = False
    channel_size = 16
    
    # Check for text patterns that indicate channel names
    if b'FRS' in data[:100] or b'GMRS' in data[:100]:
        has_names = True
        channel_size = 32
    
    # Try different configurations
    configs = [
        (0x00, False, False),  # AR-5RM: offset 0, no leading byte, with names
        (0x10, False, False),  # Standard Baofeng: offset 0x10, no leading byte
        (0x10, True, False),   # Some Baofeng: offset 0x10, with leading zero byte
    ]
    
    for start_offset, skip_byte, _ in configs:
        test_channels = []
        offset = start_offset
        channel_num = 1
        
        while offset + channel_size <= len(data):
            channel_data = data[offset:offset + channel_size]
            
            channel = parse_channel(channel_data, channel_num, has_names, skip_byte)
            if channel:
                test_channels.append(channel)
            
            offset += channel_size
            channel_num += 1
            
            # Stop after reasonable number of channels
            if channel_num > 200:
                break
        
        # Keep the result with the most channels found
        if len(test_channels) > len(channels):
            channels = test_channels
    
    return channels

def export_to_csv(channels, output_file):
    """Export channels to CSV format"""
    if not channels:
        print("No valid channels found")
        return False
    
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['channel', 'name', 'rx_freq', 'tx_freq', 'power', 'tone']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for channel in channels:
            writer.writerow(channel)
    
    return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 parse_baofeng.py <img_file> [output.csv]")
        print("\nOr to process all .img files:")
        print("  python3 parse_baofeng.py --all")
        sys.exit(1)
    
    if sys.argv[1] == '--all':
        import glob
        os.makedirs('csv', exist_ok=True)
        
        img_files = glob.glob('*.img')
        if not img_files:
            print("No .img files found")
            sys.exit(1)
        
        for img_file in img_files:
            basename = os.path.splitext(img_file)[0]
            csv_file = f"csv/{basename}.csv"
            
            print(f"Processing {img_file}...")
            channels = parse_baofeng_img(img_file)
            
            if export_to_csv(channels, csv_file):
                print(f"✓ Exported {len(channels)} channels to {csv_file}")
            else:
                print(f"✗ Failed to parse {img_file}")
    else:
        img_file = sys.argv[1]
        csv_file = sys.argv[2] if len(sys.argv) > 2 else img_file.replace('.img', '.csv')
        
        print(f"Parsing {img_file}...")
        channels = parse_baofeng_img(img_file)
        
        if export_to_csv(channels, csv_file):
            print(f"✓ Exported {len(channels)} channels to {csv_file}")
        else:
            print(f"✗ Failed to parse {img_file}")

if __name__ == '__main__':
    main()
