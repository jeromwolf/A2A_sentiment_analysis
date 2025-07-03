#!/usr/bin/env python3
"""
Simple test to verify weasyprint functionality
"""
import weasyprint

html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Test PDF</title>
</head>
<body>
    <h1>Test PDF Generation</h1>
    <p>This is a test PDF generated with WeasyPrint.</p>
</body>
</html>
"""

try:
    # Test 1: Direct PDF generation
    print("Test 1: Direct PDF generation")
    html_doc = weasyprint.HTML(string=html_content)
    pdf_content = html_doc.write_pdf()
    print(f"✅ PDF generated successfully, size: {len(pdf_content)} bytes")
    
    # Save to file
    with open("test_output.pdf", "wb") as f:
        f.write(pdf_content)
    print("✅ PDF saved to test_output.pdf")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()