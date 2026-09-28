import os
import glob
import pymupdf4llm

def parse_pdf_local(pdf_path: str):
    """
    Reads a PDF, converts each page to markdown locally.
    Uses 'pymupdf4llm' to detect tables and run OCR (Tesseract) on images/flowcharts.
    Saves the combined markdown to data/processed_chunks/{doc_id}.md
    """
    doc_id = os.path.splitext(os.path.basename(pdf_path))[0]
    out_dir = os.path.join("data", "processed_chunks")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{doc_id}.md")
    
    print(f"Processing PDF locally: {pdf_path}")
    
    # Process the PDF into markdown using pymupdf4llm
    # use_ocr=True enables automatic Tesseract OCR on areas that are images (like flowcharts).
    try:
        pages_data = pymupdf4llm.to_markdown(pdf_path, page_chunks=True, use_ocr=True)
    except Exception as e:
        print(f"Failed to parse {pdf_path} with pymupdf4llm: {e}")
        print("Note: Ensure Tesseract OCR is installed and in your system PATH.")
        return

    markdown_content = []
    
    # `pages_data` is a list of dictionaries, one per page
    for i, page_chunk in enumerate(pages_data, start=1):
        page_text = page_chunk.get("text", "").strip()
        
        # Append custom PAGE marker for our clause_chunker to track page numbers
        markdown_content.append(f"<!-- PAGE {i} -->\n{page_text}")
        
    # Save the combined markdown
    if markdown_content:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n\n".join(markdown_content))
        print(f"Successfully saved parsed Markdown to: {out_path}")
    else:
        print("No usable content found in the document.")

if __name__ == "__main__":
    # Test execution block
    raw_pdfs_dir = os.path.join("data", "raw_pdfs")
    pdf_files = glob.glob(os.path.join(raw_pdfs_dir, "*.pdf"))
    
    if pdf_files:
        print(f"Found {len(pdf_files)} PDF(s). Testing with the first one: {pdf_files[0]}")
        parse_pdf_local(pdf_files[0])
    else:
        print(f"No PDFs found in {raw_pdfs_dir}. Add a PDF to test.")
