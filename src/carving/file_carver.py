import argparse
import os

# Define file signatures (hex header -> footer)
FILE_SIGNATURES = {
    "jpg": {
        "header": bytes.fromhex("FFD8"),
        "footer": bytes.fromhex("FFD9"),
    },
    "png": {
        "header": bytes.fromhex("89504E470D0A1A0A"),
        "footer": bytes.fromhex("49454E44AE426082"),
    },
    "pdf": {
        "header": b"%PDF",
        "footer": b"%%EOF",
    },
    "zip": {
        "header": bytes.fromhex("504B0304"),
        "footer": bytes.fromhex("504B0506"),  # Simplified
    }
}


def carve_files(input_file, output_dir, types):
    print(f"[+] Reading from: {input_file}")
    with open(input_file, "rb") as f:
        data = f.read()

    count = 0
    for ftype in types:
        sig = FILE_SIGNATURES.get(ftype)
        if not sig:
            print(f"[!] Unsupported type: {ftype}")
            continue

        header = sig["header"]
        footer = sig["footer"]
        start = 0

        while True:
            head_index = data.find(header, start)
            if head_index == -1:
                break

            foot_index = data.find(footer, head_index + len(header))
            if foot_index == -1:
                print(f"[!] Footer for {ftype} not found after {head_index}. Skipping.")
                break

            end_index = foot_index + len(footer)
            carved_data = data[head_index:end_index]

            output_path = os.path.join(output_dir, f"carved_{count}.{ftype}")
            with open(output_path, "wb") as out:
                out.write(carved_data)
                print(f"[+] Carved {ftype} to: {output_path}")
                count += 1

            start = end_index

    if count == 0:
        print("[-] No files carved.")
    else:
        print(f"[✓] Total files carved: {count}")


def main():
    parser = argparse.ArgumentParser(description="🛠️ ArteFact File Carver")
    parser.add_argument("-i", "--input", required=True, help="Input disk image/raw binary file")
    parser.add_argument("-o", "--output", required=True, help="Output directory to store carved files")
    parser.add_argument('--types', nargs='+', type=str, help='File types to carve (e.g., jpg png pdf)')

    args = parser.parse_args()
    input_file = args.input
    output_dir = args.output
    types = [t.strip().lower() for t in args.types]

    if not os.path.exists(input_file):
        print(f"[✘] Input file does not exist: {input_file}")
        return

    os.makedirs(output_dir, exist_ok=True)
    carve_files(input_file, output_dir, types)


if __name__ == "__main__":
    main()
