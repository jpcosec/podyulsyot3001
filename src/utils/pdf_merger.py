import os
import subprocess
import argparse
from PyPDF2 import PdfMerger

def compress_pdf(input_path, output_path, resolution='screen'):
    """
    Compresses a PDF using ghostscript.
    Resolutions:
      screen: low resolution, smallest size
      ebook: medium resolution
      printer: high resolution
      prepress: high resolution
    """
    cmd = [
        "gs",
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS=/{resolution}",
        "-dNOPAUSE",
        "-dBATCH",
        "-dQUIET",
        f"-sOutputFile={output_path}",
        input_path
    ]
    print(f"Compressing with {resolution} settings...")
    try:
        subprocess.run(cmd, check=True)
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"Compression complete. Final size: {size_mb:.2f} MB")
        return size_mb
    except Exception as e:
        print(f"Error compressing PDF: {e}")
        return None

def merge_pdfs(pdf_list, output_path):
    print("Merging PDFs...")
    merger = PdfMerger()
    for pdf in pdf_list:
        if os.path.exists(pdf):
            print(f"Adding: {os.path.basename(pdf)}")
            merger.append(pdf)
        else:
            print(f"Warning: File not found: {pdf}")
    
    # Write to a temporary uncompressed file
    temp_path = output_path.replace(".pdf", "_uncompressed.pdf")
    merger.write(temp_path)
    merger.close()
    print(f"Merged PDF saved to {temp_path}")
    return temp_path

def main():
    parser = argparse.ArgumentParser(description="Merge and compress PDF application documents.")
    parser.add_argument("-o", "--output", default="Final_Application.pdf", help="Output file name")
    parser.add_argument("inputs", nargs="+", help="List of PDF files to merge in order")
    args = parser.parse_args()

    temp_merged = merge_pdfs(args.inputs, args.output)
    
    # Try different compression levels to get under 5MB if necessary
    for res in ["ebook", "screen"]:
        size = compress_pdf(temp_merged, args.output, resolution=res)
        if size and size < 5.0:
            print("Successfully compressed under 5MB!")
            break
        print(f"Size too large: {size:.2f} MB. Trying heavier compression...")

    # Cleanup temp
    if os.path.exists(temp_merged):
        os.remove(temp_merged)

if __name__ == "__main__":
    main()
