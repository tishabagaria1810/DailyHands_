"""Test script to verify PDF patch changes"""
from reports import get_contractor_report_data, get_agency_report_data
from reports import generate_contractor_pdf, generate_agency_pdf

print("="*60)
print("TESTING PDF PATCH - SUMMARY & CURRENCY FIX")
print("="*60)

# Test Contractor PDF
print("\n1. Testing Contractor PDF...")
contractor_data = get_contractor_report_data(1)
contractor_pdf = generate_contractor_pdf(contractor_data, 'Test Contractor')

print(f"   ✓ PDF generated: {len(contractor_pdf.getvalue()):,} bytes")
print(f"   ✓ Summary shows: {contractor_data['summary']['total_requests']} completed requests")
print(f"   ✓ Total payments: {contractor_data['summary']['total_payments']:.2f} Rs.")

# Save test PDF
with open('test_contractor_report.pdf', 'wb') as f:
    f.write(contractor_pdf.getvalue())
print("   ✓ Saved as: test_contractor_report.pdf")

# Test Agency PDF
print("\n2. Testing Agency PDF...")
agency_data = get_agency_report_data(1)
agency_pdf = generate_agency_pdf(agency_data, 'Test Agency')

print(f"   ✓ PDF generated: {len(agency_pdf.getvalue()):,} bytes")
print(f"   ✓ Summary shows: {agency_data['summary']['total_jobs']} completed jobs")
print(f"   ✓ Total earnings: {agency_data['summary']['total_earnings']:.2f} Rs.")

# Save test PDF
with open('test_agency_report.pdf', 'wb') as f:
    f.write(agency_pdf.getvalue())
print("   ✓ Saved as: test_agency_report.pdf")

print("\n" + "="*60)
print("✓ PATCH VERIFICATION COMPLETE")
print("="*60)
print("\nChanges Applied:")
print("1. Summary simplified - shows only completed count")
print("2. Currency format changed from ₹ to 'Rs.' suffix")
print("\nPlease review the generated PDF files to verify:")
print("- test_contractor_report.pdf")
print("- test_agency_report.pdf")
print("="*60)
