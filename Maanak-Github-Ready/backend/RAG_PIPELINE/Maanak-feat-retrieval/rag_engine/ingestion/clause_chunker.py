import os
import glob
import re
import json

def extract_is_number(doc_id: str) -> str:
    """
    Attempts to extract 'IS 16335:2025' from a filename like 'is_16335_2025'.
    If it doesn't match the expected pattern, returns the doc_id as uppercase.
    """
    # e.g., 'is_16335_2025' -> 'IS 16335:2025'
    parts = doc_id.split('_')
    if len(parts) >= 3 and parts[0].lower() == 'is':
        # Reconstruct something like IS 16335:2025
        # We assume the first part is IS, the second is number, the third is year
        return f"IS {parts[1]}:{parts[2]}"
    return doc_id.replace('_', ' ').upper()

def process_markdown_files():
    input_dir = os.path.join("data", "processed_chunks")
    output_dir = os.path.join("data", "metadata")
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, "chunks_dataset.json")
    
    md_files = glob.glob(os.path.join(input_dir, "*.md"))
    
    # Regex to detect page markers we added in the parser
    page_marker_pattern = re.compile(r'^<!-- PAGE (\d+) -->$')
    
    def get_clause_match(line_str):
        # Strip leading markdown symbols for easier matching
        clean = re.sub(r'^[\#\*\_\s]+', '', line_str)
        # Match clause number, then any combination of spaces, asterisks, underscores, dashes, then a Capital letter
        match = re.match(r'^([0-9]+(?:\.[0-9]+)*)[\*\_\s\-—]+([A-Z].*)', clean)
        if match:
            c_no = match.group(1)
            c_title = match.group(2).strip()
            # Clean up trailing markdown
            c_title = re.sub(r'[\*\_]+$', '', c_title)
            return c_no, c_title
        return None, None
    
    all_chunks = []
    
    for md_file in md_files:
        doc_id = os.path.splitext(os.path.basename(md_file))[0]
        is_number = extract_is_number(doc_id)
        
        with open(md_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        current_page = 1
        current_clause_no = None
        current_clause_title = None
        current_chunk_lines = []
        
        def save_chunk():
            if current_clause_no and current_chunk_lines:
                chunk_text = "\n".join(current_chunk_lines).strip()
                if chunk_text:
                    all_chunks.append({
                        "doc_id": doc_id,
                        "is_number": is_number,
                        "clause_no": current_clause_no,
                        "clause_title": current_clause_title,
                        "page_number": current_page,
                        "chunk_text": chunk_text
                    })
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                if current_clause_no is not None:
                    current_chunk_lines.append("")
                continue
                
            # Check for page marker
            page_match = page_marker_pattern.match(line_stripped)
            if page_match:
                current_page = int(page_match.group(1))
                continue
            
            # Check for clause boundary
            c_no, c_title = get_clause_match(line_stripped)
            if c_no:
                # Save previous chunk if it exists
                save_chunk()
                
                # Start new chunk
                current_clause_no = c_no
                current_clause_title = c_title
                current_chunk_lines = [line_stripped]
            else:
                # If we haven't found a clause yet, we might have introductory text.
                # We can either ignore it or save it under a generic "intro" clause.
                # Since the requirement says "split strictly at clause headings",
                # we only append if we are inside a clause.
                if current_clause_no is not None:
                    current_chunk_lines.append(line_stripped)
                    
        # Save the very last chunk
        save_chunk()

    # Save to JSON
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=4, ensure_ascii=False)
        
    print(f"Processed {len(md_files)} files. Generated {len(all_chunks)} chunks.")
    print(f"Saved dataset to {output_file}")
    
    return all_chunks

if __name__ == "__main__":
    chunks = process_markdown_files()
    if chunks:
        print("\n--- First 2 chunks ---")
        for chunk in chunks[:2]:
            print(json.dumps(chunk, indent=4))
    else:
        print("No chunks found. Ensure you have processed markdown files.")
