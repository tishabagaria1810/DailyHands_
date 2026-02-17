"""
Report Export Module for DailyHands
Handles PDF and CSV report generation with charts
"""
import io
import csv
import sqlite3
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

DATABASE = 'dailyhands.db'

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def get_date_range(start_date=None, end_date=None):
    """
    Get date range for reports
    If no dates provided, default to last 6 months (180 days)
    Returns: (start_date_str, end_date_str) in 'YYYY-MM-DD' format
    """
    if start_date and end_date:
        return start_date, end_date
    
    # Default: last 6 months
    end = datetime.now()
    start = end - timedelta(days=180)
    return start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')

def filter_data_by_date(query, params, date_field, start_date, end_date):
    """
    Add date filtering to SQL query
    """
    query += f" AND {date_field} BETWEEN ? AND ?"
    params = tuple(list(params) + [start_date, end_date])
    return query, params

# ============ CONTRACTOR REPORT FUNCTIONS ============

def get_contractor_report_data(contractor_id, start_date=None, end_date=None):
    """
    Get all report data for a contractor within date range
    """
    start_date, end_date = get_date_range(start_date, end_date)
    conn = get_db()
    cursor = conn.cursor()
    
    # Get summary statistics (completed requests only)
    cursor.execute("""
        SELECT 
            COUNT(*) as total_requests,
            COUNT(CASE WHEN status = 'Pending' THEN 1 END) as pending,
            COUNT(CASE WHEN status IN ('Accepted', 'Assigned') THEN 1 END) as active,
            COUNT(CASE WHEN status = 'Completed' THEN 1 END) as completed
        FROM work_requests 
        WHERE contractor_id = ? AND created_at BETWEEN ? AND ? AND status = 'Completed'
    """, (contractor_id, start_date, end_date))
    summary = dict(cursor.fetchone())
    
    # Get total payments (completed requests only)
    cursor.execute("""
        SELECT COALESCE(SUM(p.amount), 0) as total_payments
        FROM payments p
        JOIN work_requests wr ON p.request_id = wr.id
        WHERE wr.contractor_id = ? AND p.date BETWEEN ? AND ? AND wr.status = 'Completed'
    """, (contractor_id, start_date, end_date))
    summary['total_payments'] = cursor.fetchone()['total_payments']
    
    # Get detailed requests (completed only)
    cursor.execute("""
        SELECT wr.*, a.name as agency_name,
               (SELECT COUNT(*) FROM request_workers WHERE request_id = wr.id) as assigned_workers
        FROM work_requests wr 
        LEFT JOIN agencies a ON wr.agency_id = a.id 
        WHERE wr.contractor_id = ? AND wr.created_at BETWEEN ? AND ? AND wr.status = 'Completed'
        ORDER BY wr.created_at DESC
    """, (contractor_id, start_date, end_date))
    requests = [dict(row) for row in cursor.fetchall()]
    
    # Get monthly trend data for chart (completed only)
    cursor.execute("""
        SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as count
        FROM work_requests
        WHERE contractor_id = ? AND created_at BETWEEN ? AND ? AND status = 'Completed'
        GROUP BY month
        ORDER BY month
    """, (contractor_id, start_date, end_date))
    trend_data = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        'summary': summary,
        'requests': requests,
        'trend_data': trend_data,
        'start_date': start_date,
        'end_date': end_date
    }

# ============ AGENCY REPORT FUNCTIONS ============

def get_agency_report_data(agency_id, start_date=None, end_date=None):
    """
    Get all report data for an agency within date range
    """
    start_date, end_date = get_date_range(start_date, end_date)
    conn = get_db()
    cursor = conn.cursor()
    
    # Get summary statistics (completed jobs only)
    cursor.execute("""
        SELECT 
            COUNT(*) as total_jobs,
            COUNT(CASE WHEN status IN ('Accepted', 'Assigned') THEN 1 END) as active,
            COUNT(CASE WHEN status = 'Completed' THEN 1 END) as completed
        FROM work_requests 
        WHERE agency_id = ? AND created_at BETWEEN ? AND ? AND status = 'Completed'
    """, (agency_id, start_date, end_date))
    summary = dict(cursor.fetchone())
    
    # Get earnings summary (completed jobs only)
    cursor.execute("""
        SELECT 
            COALESCE(SUM(ae.total_earned), 0) as total_earned,
            COALESCE(SUM(ae.penalty_earned), 0) as penalty_earned
        FROM agency_earnings ae
        JOIN work_requests wr ON ae.request_id = wr.id
        WHERE ae.agency_id = ? AND wr.created_at BETWEEN ? AND ? AND wr.status = 'Completed'
    """, (agency_id, start_date, end_date))
    earnings_summary = dict(cursor.fetchone())
    summary.update(earnings_summary)
    summary['total_earnings'] = summary['total_earned'] + summary['penalty_earned']
    
    # Calculate commission (10% of total earned)
    summary['commission'] = summary['total_earned'] * 0.10
    summary['worker_payments'] = summary['total_earned'] - summary['commission']
    
    # Get detailed earnings by request (completed only)
    cursor.execute("""
        SELECT ae.*, wr.title, wr.status, wr.start_date, wr.expected_duration,
               u.name as contractor_name
        FROM agency_earnings ae
        JOIN work_requests wr ON ae.request_id = wr.id
        JOIN users u ON wr.contractor_id = u.id
        WHERE ae.agency_id = ? AND wr.created_at BETWEEN ? AND ? AND wr.status = 'Completed'
        ORDER BY wr.created_at DESC
    """, (agency_id, start_date, end_date))
    earnings_details = [dict(row) for row in cursor.fetchall()]
    
    # Get monthly earnings trend for chart (completed only)
    cursor.execute("""
        SELECT strftime('%Y-%m', wr.created_at) as month, 
               SUM(ae.total_earned) as earned,
               SUM(ae.penalty_earned) as penalty
        FROM agency_earnings ae
        JOIN work_requests wr ON ae.request_id = wr.id
        WHERE ae.agency_id = ? AND wr.created_at BETWEEN ? AND ? AND wr.status = 'Completed'
        GROUP BY month
        ORDER BY month
    """, (agency_id, start_date, end_date))
    trend_data = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        'summary': summary,
        'earnings_details': earnings_details,
        'trend_data': trend_data,
        'start_date': start_date,
        'end_date': end_date
    }

# ============ CHART GENERATION FUNCTIONS ============

def create_contractor_chart(trend_data):
    """
    Create line chart for contractor requests over time
    Returns: BytesIO object containing PNG image
    """
    if not trend_data:
        # Create empty chart
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, 'No data available for selected period', 
                ha='center', va='center', fontsize=12, color='gray')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
    else:
        months = [row['month'] for row in trend_data]
        counts = [row['count'] for row in trend_data]
        
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(months, counts, marker='o', linewidth=2, markersize=8, color='#6366f1')
        ax.fill_between(range(len(months)), counts, alpha=0.3, color='#6366f1')
        ax.set_xlabel('Month', fontsize=10)
        ax.set_ylabel('Number of Requests', fontsize=10)
        ax.set_title('Work Requests Over Time', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
    
    # Save to BytesIO
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    img_buffer.seek(0)
    plt.close()
    
    return img_buffer

def create_agency_chart(trend_data):
    """
    Create bar chart for agency earnings vs penalties over time
    Returns: BytesIO object containing PNG image
    """
    if not trend_data:
        # Create empty chart
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, 'No data available for selected period', 
                ha='center', va='center', fontsize=12, color='gray')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
    else:
        months = [row['month'] for row in trend_data]
        earned = [row['earned'] or 0 for row in trend_data]
        penalty = [row['penalty'] or 0 for row in trend_data]
        
        fig, ax = plt.subplots(figsize=(8, 4))
        x = range(len(months))
        width = 0.35
        
        ax.bar([i - width/2 for i in x], earned, width, label='Commission Earned', color='#10b981')
        ax.bar([i + width/2 for i in x], penalty, width, label='Penalty Bonus', color='#f59e0b')
        
        ax.set_xlabel('Month', fontsize=10)
        ax.set_ylabel('Amount (₹)', fontsize=10)
        ax.set_title('Earnings Breakdown Over Time', fontsize=12, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(months, rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
    
    # Save to BytesIO
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    img_buffer.seek(0)
    plt.close()
    
    return img_buffer

# ============ CSV EXPORT FUNCTIONS ============

def generate_contractor_csv(data, user_name):
    """
    Generate CSV report for contractor
    Returns: BytesIO object containing CSV data
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header section
    writer.writerow(['DailyHands - Work Request Summary Report'])
    writer.writerow(['Contractor:', user_name])
    writer.writerow(['Period:', f"{data['start_date']} to {data['end_date']}"])
    writer.writerow(['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    writer.writerow([])
    
    # Summary section
    writer.writerow(['SUMMARY'])
    writer.writerow(['Total Requests', data['summary']['total_requests']])
    writer.writerow(['Pending', data['summary']['pending']])
    writer.writerow(['Active', data['summary']['active']])
    writer.writerow(['Completed', data['summary']['completed']])
    writer.writerow(['Total Payments', f"₹{data['summary']['total_payments']:.2f}"])
    writer.writerow([])
    
    # Detailed requests table
    writer.writerow(['DETAILED REQUESTS'])
    writer.writerow(['Title', 'Status', 'Agency', 'Worker Type', 'Workers Needed', 
                     'Wage/Day', 'Duration (days)', 'Start Date', 'Assigned Workers'])
    
    for req in data['requests']:
        writer.writerow([
            req['title'],
            req['status'],
            req['agency_name'] or 'Not assigned',
            req['worker_type'],
            req['workers_needed'],
            f"₹{req['wage_per_day']:.2f}",
            req['expected_duration'],
            req['start_date'],
            req['assigned_workers']
        ])
    
    # Convert to BytesIO
    output.seek(0)
    csv_buffer = io.BytesIO()
    csv_buffer.write(output.getvalue().encode('utf-8-sig'))  # UTF-8 with BOM for Excel
    csv_buffer.seek(0)
    
    return csv_buffer

def generate_agency_csv(data, agency_name):
    """
    Generate CSV report for agency
    Returns: BytesIO object containing CSV data
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header section
    writer.writerow(['DailyHands - Agency Earnings Report'])
    writer.writerow(['Agency:', agency_name])
    writer.writerow(['Period:', f"{data['start_date']} to {data['end_date']}"])
    writer.writerow(['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    writer.writerow([])
    
    # Summary section
    writer.writerow(['SUMMARY'])
    writer.writerow(['Total Jobs', data['summary']['total_jobs']])
    writer.writerow(['Active Jobs', data['summary']['active']])
    writer.writerow(['Completed Jobs', data['summary']['completed']])
    writer.writerow(['Total Earned', f"₹{data['summary']['total_earned']:.2f}"])
    writer.writerow(['Penalty Bonus', f"₹{data['summary']['penalty_earned']:.2f}"])
    writer.writerow(['Total Earnings', f"₹{data['summary']['total_earnings']:.2f}"])
    writer.writerow(['Agency Commission (10%)', f"₹{data['summary']['commission']:.2f}"])
    writer.writerow(['Worker Payments', f"₹{data['summary']['worker_payments']:.2f}"])
    writer.writerow([])
    
    # Detailed earnings table
    writer.writerow(['EARNINGS BY REQUEST'])
    writer.writerow(['Request Title', 'Contractor', 'Status', 'Start Date', 
                     'Duration (days)', 'Total Earned', 'Penalty Earned', 'Total'])
    
    for earning in data['earnings_details']:
        total = earning['total_earned'] + earning['penalty_earned']
        writer.writerow([
            earning['title'],
            earning['contractor_name'],
            earning['status'],
            earning['start_date'],
            earning['expected_duration'],
            f"₹{earning['total_earned']:.2f}",
            f"₹{earning['penalty_earned']:.2f}",
            f"₹{total:.2f}"
        ])
    
    # Convert to BytesIO
    output.seek(0)
    csv_buffer = io.BytesIO()
    csv_buffer.write(output.getvalue().encode('utf-8-sig'))  # UTF-8 with BOM for Excel
    csv_buffer.seek(0)
    
    return csv_buffer

# ============ PDF EXPORT FUNCTIONS ============

def generate_contractor_pdf(data, user_name):
    """
    Generate PDF report for contractor with embedded chart
    Returns: BytesIO object containing PDF data
    """
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=A4, 
                           rightMargin=0.75*inch, leftMargin=0.75*inch,
                           topMargin=0.75*inch, bottomMargin=0.75*inch)
    
    # Container for PDF elements
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#6366f1'),
        spaceAfter=12,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=10,
        spaceBefore=15
    )
    
    # Header
    elements.append(Paragraph('DailyHands', title_style))
    elements.append(Paragraph('Work Request Summary Report', styles['Heading2']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Report metadata
    meta_data = [
        ['Contractor:', user_name],
        ['Period:', f"{data['start_date']} to {data['end_date']}"],
        ['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
    ]
    meta_table = Table(meta_data, colWidths=[1.5*inch, 4*inch])
    meta_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#4b5563')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Summary section
    elements.append(Paragraph('Summary', heading_style))
    summary_data = [
        ['Metric', 'Value'],
        ['Total Completed Requests', str(data['summary']['total_requests'])],
        ['Total Payments', f"{data['summary']['total_payments']:.2f} Rs."]
    ]
    summary_table = Table(summary_data, colWidths=[3*inch, 2.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6366f1')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')])
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Chart
    elements.append(Paragraph('Requests Over Time', heading_style))
    chart_img = create_contractor_chart(data['trend_data'])
    img = Image(chart_img, width=5.5*inch, height=2.75*inch)
    elements.append(img)
    elements.append(Spacer(1, 0.3*inch))
    
    # Detailed requests table
    elements.append(Paragraph('Detailed Requests', heading_style))
    
    if data['requests']:
        # Table headers
        table_data = [['Title', 'Status', 'Agency', 'Workers', 'Wage/Day', 'Start Date']]
        
        # Table rows
        for req in data['requests']:
            table_data.append([
                Paragraph(req['title'][:30], styles['Normal']),
                req['status'],
                Paragraph((req['agency_name'] or 'Not assigned')[:20], styles['Normal']),
                f"{req['assigned_workers']}/{req['workers_needed']}",
                f"{req['wage_per_day']:.0f} Rs.",
                req['start_date']
            ])
        
        requests_table = Table(table_data, colWidths=[1.5*inch, 0.9*inch, 1.3*inch, 0.7*inch, 0.8*inch, 1*inch])
        requests_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6366f1')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')])
        ]))
        elements.append(requests_table)
    else:
        elements.append(Paragraph('No requests found for the selected period.', styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    pdf_buffer.seek(0)
    
    return pdf_buffer

def generate_agency_pdf(data, agency_name):
    """
    Generate PDF report for agency with embedded chart
    Returns: BytesIO object containing PDF data
    """
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=A4, 
                           rightMargin=0.75*inch, leftMargin=0.75*inch,
                           topMargin=0.75*inch, bottomMargin=0.75*inch)
    
    # Container for PDF elements
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#10b981'),
        spaceAfter=12,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=10,
        spaceBefore=15
    )
    
    # Header
    elements.append(Paragraph('DailyHands', title_style))
    elements.append(Paragraph('Agency Earnings Report', styles['Heading2']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Report metadata
    meta_data = [
        ['Agency:', agency_name],
        ['Period:', f"{data['start_date']} to {data['end_date']}"],
        ['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
    ]
    meta_table = Table(meta_data, colWidths=[1.5*inch, 4*inch])
    meta_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#4b5563')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Summary section
    elements.append(Paragraph('Summary', heading_style))
    summary_data = [
        ['Metric', 'Value'],
        ['Total Completed Jobs', str(data['summary']['total_jobs'])],
        ['Commission Earned', f"{data['summary']['total_earned']:.2f} Rs."],
        ['Penalty Bonus', f"{data['summary']['penalty_earned']:.2f} Rs."],
        ['Total Earnings', f"{data['summary']['total_earnings']:.2f} Rs."],
        ['Agency Commission (10%)', f"{data['summary']['commission']:.2f} Rs."],
        ['Worker Payments', f"{data['summary']['worker_payments']:.2f} Rs."]
    ]
    summary_table = Table(summary_data, colWidths=[3*inch, 2.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')])
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Chart
    elements.append(Paragraph('Earnings Breakdown Over Time', heading_style))
    chart_img = create_agency_chart(data['trend_data'])
    img = Image(chart_img, width=5.5*inch, height=2.75*inch)
    elements.append(img)
    elements.append(Spacer(1, 0.3*inch))
    
    # Detailed earnings table
    elements.append(Paragraph('Earnings by Request', heading_style))
    
    if data['earnings_details']:
        # Table headers
        table_data = [['Request', 'Contractor', 'Status', 'Earned', 'Penalty', 'Total']]
        
        # Table rows
        for earning in data['earnings_details']:
            total = earning['total_earned'] + earning['penalty_earned']
            table_data.append([
                Paragraph(earning['title'][:25], styles['Normal']),
                Paragraph(earning['contractor_name'][:20], styles['Normal']),
                earning['status'],
                f"{earning['total_earned']:.0f} Rs.",
                f"{earning['penalty_earned']:.0f} Rs.",
                f"{total:.0f} Rs."
            ])
        
        earnings_table = Table(table_data, colWidths=[1.8*inch, 1.5*inch, 1*inch, 0.9*inch, 0.9*inch, 0.9*inch])
        earnings_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')])
        ]))
        elements.append(earnings_table)
    else:
        elements.append(Paragraph('No earnings data found for the selected period.', styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    pdf_buffer.seek(0)
    
    return pdf_buffer
