#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Export each PDF page as a preview JPEG for visual inspection."""

import os
import sys
from pathlib import Path

# We'll regenerate and capture the pages from the build function
# by monkey-patching the save step.

import build_process_pdf_v2 as bp
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
PREVIEW_DIR = ROOT / "pdf_preview"

def build_and_export():
    """Build PDF and also export individual page JPEGs."""
    os.makedirs(str(PREVIEW_DIR), exist_ok=True)
    
    # We need to intercept the pages. The simplest way:
    # Copy the build_pdf function's page generation and save each page.
    # But that's complex. Instead, let's modify build_pdf to return pages.
    
    # Actually, let's just call the internals directly.
    # The build_pdf function creates pages list and saves. 
    # We'll re-run build_pdf but capture pages by hooking.
    
    import types
    
    original_save = Image.Image.save
    pages_captured = []
    
    # Temporarily override to capture
    # Actually, let's just re-implement the save part.
    # Simpler: read the source, the function builds pages[] then saves.
    # Let's just exec the function and capture the local 'pages' variable.
    
    # Simplest approach: modify build_pdf to return pages
    # But we shouldn't modify the file. Let's use a different approach.
    
    # Re-run the function and intercept the PDF save call
    class PageCapture:
        def __init__(self):
            self.pages = []
        
    capture = PageCapture()
    
    # Monkey-patch pages[0].save to capture
    original_method = Image.Image.save.__func__ if hasattr(Image.Image.save, '__func__') else Image.Image.save
    
    def patched_save(self, fp, format=None, **params):
        if format == "PDF" and params.get("save_all"):
            capture.pages = [self] + list(params.get("append_images", []))
        return original_method(self, fp, format, **params)
    
    Image.Image.save = patched_save
    try:
        bp.build_pdf()
    finally:
        Image.Image.save = original_method
    
    # Export each page
    for i, page in enumerate(capture.pages):
        out_path = PREVIEW_DIR / "page-{:02d}.jpg".format(i + 1)
        page.convert("RGB").save(str(out_path), "JPEG", quality=85)
        
        # Also save hires version
        hires_path = PREVIEW_DIR / "hires-{:02d}.jpg".format(i + 1)
        page.convert("RGB").save(str(hires_path), "JPEG", quality=92)
        
    print("Exported {} pages to {}".format(len(capture.pages), PREVIEW_DIR))

if __name__ == "__main__":
    build_and_export()
