"""
Export tool for saving trip itineraries to files.
In production, this would integrate with Google Docs/Sheets API.
"""

import os
from datetime import datetime


def export_itinerary_to_doc(itinerary_content: str, filename: str = None) -> dict:
    """
    Exports the final trip itinerary to a document file.
    
    This tool saves the complete itinerary (flights, hotels, activities, costs)
    to a markdown file that can be easily shared or imported into Google Docs.
    
    Args:
        itinerary_content: The complete itinerary in markdown format
        filename: Optional custom filename. Defaults to 'trip_itinerary_YYYYMMDD.md'
    
    Returns:
        A dictionary with 'status' and 'filepath' indicating where the file was saved.
    """
    print(f"TOOL CALLED: export_itinerary_to_doc(filename='{filename}')")
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"trip_itinerary_{timestamp}.md"
    
    # Ensure .md extension
    if not filename.endswith('.md'):
        filename += '.md'
    
    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.join(os.getcwd(), "itineraries")
        os.makedirs(output_dir, exist_ok=True)
        
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(itinerary_content)
        
        return {
            "status": "success",
            "filepath": filepath,
            "message": f"Itinerary successfully exported to {filename}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to export itinerary: {str(e)}"
        }

