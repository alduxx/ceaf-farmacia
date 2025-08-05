# Multiple PDFs Feature Implementation

## Overview

This feature enhancement allows the CEAF scraper to handle conditions that have multiple PDF protocols. Instead of only processing the first PDF found, the scraper now:

1. **Finds all matching PDFs** for each condition
2. **Creates separate condition entries** for each PDF
3. **Processes each PDF independently** with its own extracted data
4. **Generates custom descriptions** combining medications and CID-10 codes

## Example Case: Epilepsia

The epilepsia condition (`https://www.saude.df.gov.br/epilepsia`) has multiple PDFs:
- **Epilepsia-MS** 
- **Epilepsia-SES/DF**
- **Epilepsia Canabidiol SES-DF**

With this feature, instead of creating 1 condition entry, the scraper now creates 3 separate entries, each with data extracted from its respective PDF.

## Implementation Details

### New Methods Added

#### `find_condition_pdfs(condition_url, condition_name) -> List[Dict]`
- Finds **ALL** PDFs for a condition that match the condition name
- Returns list of PDF links with match scores
- Sorts by relevance (highest match score first)

#### `create_custom_description(condition) -> str`
- Creates custom description format as specified:
  - Medications (comma separated)
  - Line break
  - CID-10 codes (comma separated)

### Modified Logic

#### Enhanced `scrape_all_conditions()` Method
1. **For each base condition:**
   - Find all matching PDFs using `find_condition_pdfs()`
   
2. **Process first PDF:**
   - Extract data normally
   - Create condition entry with full data
   - Apply custom description format

3. **Process additional PDFs:**
   - For each additional PDF, create a **duplicate condition**
   - Remove PDF-specific data from the base condition
   - Process the new PDF independently
   - Extract fresh structured data
   - Apply custom description format
   - Add as separate condition entry

## Data Structure Changes

### New Fields Added
- `pdf_name`: Name/label of the specific PDF being processed
- `base_conditions_count`: Number of original conditions before PDF duplication

### Custom Description Format
```
medicamento1, medicamento2, medicamento3
CID-10-1, CID-10-2, CID-10-3
```

## Testing

### Test Scripts Created
1. **`test_multiple_pdfs.py`** - Unit test with mock data
2. **`demo_multiple_pdfs.py`** - Real data demonstration

### Test Results
✅ Successfully finds 3 PDFs for epilepsia condition  
✅ Creates 3 separate condition entries (1 base + 2 additional)  
✅ Each entry has independent extracted data  
✅ Custom description format is applied correctly  

## Usage

### Enhanced Scraper Scripts
All existing enhanced scraper scripts now support multiple PDFs:

```bash
# Test with limited conditions
python run_enhanced_scraper.py --limit 5

# Full scraping with multiple PDF support
python run_full_enhanced_scraper.py

# Demo the multiple PDF functionality
python demo_multiple_pdfs.py
```

### Output Changes
The scraper now reports:
- **Total conditions**: Final number including duplicates
- **Base conditions**: Original conditions from the website  
- **Additional conditions from multiple PDFs**: Number of extra entries created

## Example Output

Before (single PDF per condition):
```
📊 Total conditions: 97
📄 PDF processing: 85/97 successful
```

After (multiple PDFs per condition):
```
📊 Total conditions: 115
📊 Base conditions: 97
📑 Additional conditions from multiple PDFs: 18
📄 PDF processing: 103/115 successful
```

## Benefits

1. **Complete Coverage**: No PDF protocols are missed
2. **Separate Processing**: Each PDF gets independent data extraction
3. **Enhanced Search**: Users can search by specific protocol variants
4. **Better Organization**: Clear distinction between different protocol versions

## Backward Compatibility

✅ **Fully backward compatible**  
- Legacy `find_condition_pdf()` method still works (returns first PDF)
- Existing data structures remain unchanged
- All existing functionality continues to work

## Files Modified

- `src/scraper.py` - Core implementation
- `run_enhanced_scraper.py` - Updated reporting
- `run_full_enhanced_scraper.py` - Updated reporting

## Files Added

- `test_multiple_pdfs.py` - Unit tests
- `demo_multiple_pdfs.py` - Real data demo
- `MULTIPLE_PDFS_FEATURE.md` - This documentation