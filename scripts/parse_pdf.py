import pdfplumber
import os

def extract_page_text(page_object, page_number):
    """
    Extracts text from a single page of a PDF, inserting placeholders for images and charts.
    Ensures a newline at the end if any content is produced.
    """
    content_parts = []
    page_text_content = page_object.extract_text() # Extract text once
    if page_text_content and page_text_content.strip(): # Add actual text if present and not just whitespace
        content_parts.append(page_text_content.strip())

    # Add placeholders for images
    if page_object.images:
        for i, img in enumerate(page_object.images):
            content_parts.append(f"[IMAGE_PLACEHOLDER_{page_number + 1}_{i+1}]")

    # Add placeholders for charts
    if page_object.extract_tables():
        for i, table_data in enumerate(page_object.extract_tables()):
            content_parts.append(f"[CHART_OR_TABLE_PLACEHOLDER_{page_number + 1}_{i+1}]")

    if content_parts: # If any content (text or placeholders) was added
        return "\n".join(content_parts) + "\n" # Join parts with newline, and add a final newline
    return "" # Return empty string if page was truly blank (no text, no images, no tables)

def read_pdf_single_page(pdf_path: str, page_number: int) -> str:
    """
    Reads text from a single specified page of a PDF file.
    Page numbers are 1-based for user input, converted to 0-based for pdfplumber.
    """
    if not os.path.exists(pdf_path):
        return "Error: PDF file not found."
    if page_number <= 0:
        return "Error: Page number must be positive."

    try:
        with pdfplumber.open(pdf_path) as pdf:
            if page_number > len(pdf.pages):
                return f"Error: Page number {page_number} exceeds total pages ({len(pdf.pages)})."
            page_obj = pdf.pages[page_number - 1] # Convert to 0-indexed
            return extract_page_text(page_obj, page_number - 1)
    except Exception as e:
        return f"Error processing PDF: {e}"

def read_pdf_multiple_pages(pdf_path: str, page_numbers: list[int]) -> str:
    """
    Reads text from a list of specified pages of a PDF file.
    Page numbers are 1-based for user input.
    """
    if not os.path.exists(pdf_path):
        return "Error: PDF file not found."

    all_text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            max_page = len(pdf.pages)
            for pn in sorted(list(set(page_numbers))): # Sort and remove duplicates
                if pn <= 0:
                    all_text += f"Warning: Page number {pn} is invalid. Skipping.\n"
                    continue
                if pn > max_page:
                    all_text += f"Warning: Page number {pn} exceeds total pages ({max_page}). Skipping.\n"
                    continue
                page_obj = pdf.pages[pn - 1] # Convert to 0-indexed
                all_text += f"--- Page {pn} ---\n"
                all_text += extract_page_text(page_obj, pn - 1)
                all_text += "\n"
        return all_text
    except Exception as e:
        return f"Error processing PDF: {e}"

def read_all_pdf_pages(pdf_path: str) -> str:
    """
    Reads text from all pages of a PDF file.
    """
    if not os.path.exists(pdf_path):
        return "Error: PDF file not found."

    all_text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            all_text += f"Total pages in PDF: {total_pages}\n\n"
            for i, page_obj in enumerate(pdf.pages):
                page_content = extract_page_text(page_obj, i)
                if page_content: # Only add content if the page is not blank
                    all_text += f"--- Page {i + 1} ---\n"
                    all_text += page_content # extract_page_text already adds a newline if content exists
                    # all_text += "\n" # No longer needed here as extract_page_text handles it
                else:
                    all_text += f"--- Page {i + 1} (Blank) ---\n\n"
        return all_text
    except Exception as e:
        return f"Error processing PDF: {e}"

def save_text_to_markdown(text_content: str, output_md_path: str):
    """
    Saves the given text content to a Markdown file.
    """
    try:
        # Ensure the directory for the output file exists
        output_dir = os.path.dirname(output_md_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        with open(output_md_path, "w", encoding="utf-8") as f:
            f.write(text_content)
        return f"Successfully saved to {output_md_path}"
    except Exception as e:
        return f"Error saving to Markdown: {e}"

if __name__ == "__main__":
    # Create a dummy PDF in downloads for testing if it doesn't exist
    # For a real scenario, the PDF would already be there.
    # This example uses the PDF mentioned in the environment details.
    
    # Determine the script's directory
    script_file_path = os.path.abspath(__file__)
    script_dir = os.path.dirname(script_file_path)

    # Path to the downloads directory, relative to the script's parent directory
    sample_pdf_dir = os.path.join(script_dir, "..", "downloads") # This will correctly point to f:/MSVAI/downloads
    sample_pdf_name = "Invoice_INV_DEU_3000001724_1746012272468.pdf"
    sample_pdf_path = os.path.join(sample_pdf_dir, sample_pdf_name)

    # We assume 'f:/MSVAI/downloads/' already exists and won't try to create it.
    # if not os.path.exists(sample_pdf_dir):
    #     os.makedirs(sample_pdf_dir)

    # Check if the sample PDF exists, if not, create a simple one for testing.
    # This is a very basic PDF creation for testing purposes.
    # In a real environment, you'd use an existing PDF.
    if not os.path.exists(sample_pdf_path):
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            c = canvas.Canvas(sample_pdf_path, pagesize=letter)
            c.drawString(72, 800, "Page 1: This is a test PDF for parse_pdf.py.")
            c.drawString(72, 780, "It contains some text.")
            # Add a simple shape that pdfplumber might see as an object
            c.rect(100, 700, 50, 50, fill=1) 
            c.showPage()
            c.drawString(72, 800, "Page 2: More text on the second page.")
            c.drawString(72, 780, "And another placeholder item.")
            c.rect(200, 600, 80, 30, fill=0, stroke=1)
            c.showPage()
            c.save()
            print(f"Created a dummy PDF for testing: {sample_pdf_path}")
        except ImportError:
            print("ReportLab not found. Skipping dummy PDF creation. Please place a PDF at " + sample_pdf_path + " for testing.")
        except Exception as e:
            print(f"Could not create dummy PDF: {e}")


    if os.path.exists(sample_pdf_path):
        print(f"--- Testing with PDF: {sample_pdf_path} ---")

        # Test 1: Read a single page (e.g., page 1)
        print("\n--- Test 1: Reading Page 1 ---")
        page_1_text = read_pdf_single_page(sample_pdf_path, 1)
        print(page_1_text)
        save_text_to_markdown(page_1_text, "output_page_1.md")
        print(f"Saved page 1 to output_page_1.md")

        # Test 2: Read multiple pages (e.g., pages 1 and 2)
        print("\n--- Test 2: Reading Pages 1 & 2 ---")
        pages_1_2_text = read_pdf_multiple_pages(sample_pdf_path, [1, 2])
        print(pages_1_2_text)
        save_text_to_markdown(pages_1_2_text, "output_pages_1_2.md")
        print(f"Saved pages 1 & 2 to output_pages_1_2.md")

        # Test 3: Read all pages
        print("\n--- Test 3: Reading All Pages ---")
        all_pages_text = read_all_pdf_pages(sample_pdf_path)
        print(all_pages_text)
        save_text_to_markdown(all_pages_text, "output_all_pages.md")
        print(f"Saved all pages to output_all_pages.md")
        
        # Test 4: Read non-existent page
        print("\n--- Test 4: Reading Non-existent Page (e.g., Page 10) ---")
        non_existent_page_text = read_pdf_single_page(sample_pdf_path, 10)
        print(non_existent_page_text)

        # Test 5: Read with invalid page number
        print("\n--- Test 5: Reading Invalid Page Number (e.g., Page 0) ---")
        invalid_page_text = read_pdf_single_page(sample_pdf_path, 0)
        print(invalid_page_text)
    else:
        print(f"Sample PDF not found at {sample_pdf_path}. Please place a PDF there to run the example usage.")

    print("\n--- Script execution finished ---")
