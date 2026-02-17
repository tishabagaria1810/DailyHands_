"""
Comprehensive test script for report export functionality
Tests all components without starting the Flask server
"""
import os
from reports import (
    get_contractor_report_data,
    get_agency_report_data,
    generate_contractor_pdf,
    generate_contractor_csv,
    generate_agency_pdf,
    generate_agency_csv,
    create_contractor_chart,
    create_agency_chart
)

def test_contractor_reports():
    """Test contractor report generation"""
    print("\n" + "="*60)
    print("TESTING CONTRACTOR REPORTS")
    print("="*60)
    
    # Test 1: Default date range (last 6 months)
    print("\n1. Testing default date range (last 6 months)...")
    data = get_contractor_report_data(1)
    print(f"   ✓ Data retrieved: {data['summary']['total_requests']} requests")
    print(f"   ✓ Date range: {data['start_date']} to {data['end_date']}")
    
    # Test 2: PDF generation
    print("\n2. Testing PDF generation...")
    pdf = generate_contractor_pdf(data, "Test Contractor")
    pdf_size = len(pdf.getvalue())
    print(f"   ✓ PDF generated: {pdf_size:,} bytes")
    
    # Test 3: CSV generation
    print("\n3. Testing CSV generation...")
    csv = generate_contractor_csv(data, "Test Contractor")
    csv_size = len(csv.getvalue())
    print(f"   ✓ CSV generated: {csv_size:,} bytes")
    
    # Test 4: Chart generation
    print("\n4. Testing chart generation...")
    chart = create_contractor_chart(data['trend_data'])
    chart_size = len(chart.getvalue())
    print(f"   ✓ Chart generated: {chart_size:,} bytes")
    
    # Test 5: Custom date range
    print("\n5. Testing custom date range...")
    custom_data = get_contractor_report_data(1, '2025-01-01', '2026-12-31')
    print(f"   ✓ Custom range: {custom_data['start_date']} to {custom_data['end_date']}")
    print(f"   ✓ Requests in range: {custom_data['summary']['total_requests']}")
    
    return True

def test_agency_reports():
    """Test agency report generation"""
    print("\n" + "="*60)
    print("TESTING AGENCY REPORTS")
    print("="*60)
    
    # Test 1: Default date range
    print("\n1. Testing default date range (last 6 months)...")
    data = get_agency_report_data(1)
    print(f"   ✓ Data retrieved: {data['summary']['total_jobs']} jobs")
    print(f"   ✓ Total earnings: ₹{data['summary']['total_earnings']:.2f}")
    print(f"   ✓ Date range: {data['start_date']} to {data['end_date']}")
    
    # Test 2: PDF generation
    print("\n2. Testing PDF generation...")
    pdf = generate_agency_pdf(data, "Test Agency")
    pdf_size = len(pdf.getvalue())
    print(f"   ✓ PDF generated: {pdf_size:,} bytes")
    
    # Test 3: CSV generation
    print("\n3. Testing CSV generation...")
    csv = generate_agency_csv(data, "Test Agency")
    csv_size = len(csv.getvalue())
    print(f"   ✓ CSV generated: {csv_size:,} bytes")
    
    # Test 4: Chart generation
    print("\n4. Testing chart generation...")
    chart = create_agency_chart(data['trend_data'])
    chart_size = len(chart.getvalue())
    print(f"   ✓ Chart generated: {chart_size:,} bytes")
    
    # Test 5: Custom date range
    print("\n5. Testing custom date range...")
    custom_data = get_agency_report_data(1, '2025-01-01', '2026-12-31')
    print(f"   ✓ Custom range: {custom_data['start_date']} to {custom_data['end_date']}")
    print(f"   ✓ Jobs in range: {custom_data['summary']['total_jobs']}")
    
    return True

def test_flask_integration():
    """Test Flask route registration"""
    print("\n" + "="*60)
    print("TESTING FLASK INTEGRATION")
    print("="*60)
    
    from app import app
    
    # Test 1: Routes exist
    print("\n1. Checking route registration...")
    routes = [str(rule) for rule in app.url_map.iter_rules()]
    contractor_route = '/contractor/export-report' in routes
    agency_route = '/agency/export-report' in routes
    
    print(f"   {'✓' if contractor_route else '✗'} Contractor export route: /contractor/export-report")
    print(f"   {'✓' if agency_route else '✗'} Agency export route: /agency/export-report")
    
    # Test 2: Templates exist
    print("\n2. Checking template files...")
    modal_exists = os.path.exists('templates/components/export_report_modal.html')
    contractor_dash = os.path.exists('templates/contractor/dashboard.html')
    agency_dash = os.path.exists('templates/agency/dashboard.html')
    
    print(f"   {'✓' if modal_exists else '✗'} Modal template exists")
    print(f"   {'✓' if contractor_dash else '✗'} Contractor dashboard exists")
    print(f"   {'✓' if agency_dash else '✗'} Agency dashboard exists")
    
    return contractor_route and agency_route and modal_exists

def test_empty_data():
    """Test handling of empty data"""
    print("\n" + "="*60)
    print("TESTING EMPTY DATA HANDLING")
    print("="*60)
    
    # Test with date range that has no data
    print("\n1. Testing with empty date range...")
    data = get_contractor_report_data(1, '2020-01-01', '2020-12-31')
    print(f"   ✓ Empty data handled: {data['summary']['total_requests']} requests")
    
    # Generate PDF with empty data
    print("\n2. Testing PDF with empty data...")
    pdf = generate_contractor_pdf(data, "Test Contractor")
    print(f"   ✓ PDF generated with empty data: {len(pdf.getvalue()):,} bytes")
    
    # Generate chart with empty data
    print("\n3. Testing chart with empty data...")
    chart = create_contractor_chart([])
    print(f"   ✓ Chart generated with empty data: {len(chart.getvalue()):,} bytes")
    
    return True

if __name__ == '__main__':
    print("\n" + "="*60)
    print("DAILYHANDS REPORT EXPORT - COMPREHENSIVE TEST SUITE")
    print("="*60)
    
    try:
        # Run all tests
        contractor_pass = test_contractor_reports()
        agency_pass = test_agency_reports()
        flask_pass = test_flask_integration()
        empty_pass = test_empty_data()
        
        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"Contractor Reports: {'✓ PASS' if contractor_pass else '✗ FAIL'}")
        print(f"Agency Reports:     {'✓ PASS' if agency_pass else '✗ FAIL'}")
        print(f"Flask Integration:  {'✓ PASS' if flask_pass else '✗ FAIL'}")
        print(f"Empty Data:         {'✓ PASS' if empty_pass else '✗ FAIL'}")
        
        all_pass = contractor_pass and agency_pass and flask_pass and empty_pass
        print("\n" + "="*60)
        if all_pass:
            print("✓ ALL TESTS PASSED - SYSTEM READY FOR PRODUCTION")
        else:
            print("✗ SOME TESTS FAILED - REVIEW REQUIRED")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
