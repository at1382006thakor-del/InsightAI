import os
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for headless execution
import matplotlib.pyplot as plt
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Tuple

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from ..database.models import Sale, Product, Customer

# Output directory for reports
REPORTS_DIR = "reports"
SCRATCH_DIR = os.path.join(REPORTS_DIR, "scratch")
os.makedirs(SCRATCH_DIR, exist_ok=True)

def generate_report_plots(db: Session) -> Tuple[str, str]:
    """Generates trend and region charts with a clean styling to embed in the PDF."""
    plt.style.use('dark_background')
    
    # 1. Trend Query
    trend_results = db.query(
        func.strftime("%Y-%m", Sale.order_date).label("month"),
        func.sum(Sale.revenue).label("revenue")
    ).group_by("month").order_by("month").all()
    
    months = [r[0] for r in trend_results]
    revenues = [float(r[1] or 0.0) for r in trend_results]

    fig, ax = plt.subplots(figsize=(6, 3))
    ax.plot(months, revenues, color="#8b5cf6", marker="o", linewidth=2)
    ax.fill_between(months, revenues, color="#8b5cf6", alpha=0.15)
    ax.set_title("Historical Sales Revenue Trend ($)", fontsize=10, color="#f4f4f5")
    ax.tick_params(colors="#a1a1aa", labelsize=8)
    plt.xticks(rotation=45)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color("#3f3f46")
    ax.spines['bottom'].set_color("#3f3f46")
    plt.tight_layout()
    
    trend_chart_path = os.path.join(SCRATCH_DIR, "trend_chart.png")
    plt.savefig(trend_chart_path, dpi=150, transparent=True)
    plt.close()

    # 2. Regional Query
    region_results = db.query(
        Sale.region,
        func.sum(Sale.revenue).label("revenue")
    ).group_by(Sale.region).all()
    
    regions = [r[0] for r in region_results]
    reg_revenues = [float(r[1] or 0.0) for r in region_results]

    fig, ax = plt.subplots(figsize=(6, 3))
    colors_list = ["#8b5cf6", "#a78bfa", "#c084fc", "#ddd6fe"]
    ax.bar(regions, reg_revenues, color=colors_list[:len(regions)], width=0.5)
    ax.set_title("Revenue by Region ($)", fontsize=10, color="#f4f4f5")
    ax.tick_params(colors="#a1a1aa", labelsize=8)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color("#3f3f46")
    ax.spines['bottom'].set_color("#3f3f46")
    plt.tight_layout()
    
    region_chart_path = os.path.join(SCRATCH_DIR, "region_chart.png")
    plt.savefig(region_chart_path, dpi=150, transparent=True)
    plt.close()

    return trend_chart_path, region_chart_path

def convert_markdown_to_pdf_paragraphs(text: str, normal_style: ParagraphStyle, bold_style: ParagraphStyle, h1_style: ParagraphStyle, h2_style: ParagraphStyle) -> list:
    """Converts a basic markdown text into a list of styled ReportLab Flowables."""
    flowables = []
    lines = text.split("\n")
    
    for line in lines:
        line = line.strip()
        if not line:
            flowables.append(Spacer(1, 0.08 * inch))
            continue
            
        if line.startswith("# "):
            clean_text = line[2:].replace("**", "").replace("*", "")
            flowables.append(Paragraph(clean_text, h1_style))
            flowables.append(Spacer(1, 0.15 * inch))
        elif line.startswith("## "):
            clean_text = line[3:].replace("**", "").replace("*", "")
            flowables.append(Paragraph(clean_text, h2_style))
            flowables.append(Spacer(1, 0.1 * inch))
        elif line.startswith("### "):
            clean_text = line[4:].replace("**", "").replace("*", "")
            flowables.append(Paragraph(f"<b>{clean_text}</b>", bold_style))
            flowables.append(Spacer(1, 0.05 * inch))
        elif line.startswith("- ") or line.startswith("* "):
            clean_text = line[2:]
            # Replace bold markdown with matching HTML tags
            import re
            clean_text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", clean_text)
            flowables.append(Paragraph(f"&bull; {clean_text}", normal_style))
        else:
            # Replace bold markdown with matching HTML tags
            import re
            clean_text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", line)
            flowables.append(Paragraph(clean_text, normal_style))
            
    return flowables

def build_pdf_report(db: Session, report_type: str, markdown_summary: str) -> str:
    """Compiles statistics, plots charts, and writes a multi-page PDF report."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_filename = f"InsightAI_{report_type.capitalize()}_Report_{timestamp}.pdf"
    pdf_path = os.path.join(REPORTS_DIR, pdf_filename)
    
    # 1. Setup Document Layout
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    # 2. Setup Styles
    styles = getSampleStyleSheet()
    
    # Custom Brand Palette
    brand_color = colors.HexColor("#7c3aed")
    text_color = colors.HexColor("#1f2937") # Charcoal for clean print
    muted_color = colors.HexColor("#4b5563")

    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=26,
        leading=30,
        textColor=brand_color,
        spaceAfter=15
    )
    
    subtitle_style = ParagraphStyle(
        'ReportSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=muted_color,
        spaceAfter=30
    )
    
    h1_style = ParagraphStyle(
        'Heading1Custom',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=brand_color,
        spaceBefore=15,
        spaceAfter=10,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#4c1d95"),
        spaceBefore=10,
        spaceAfter=5,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'BodyCustom',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=text_color,
        spaceAfter=6
    )

    bold_body_style = ParagraphStyle(
        'BoldBodyCustom',
        parent=body_style,
        fontName='Helvetica-Bold'
    )

    story = []

    # --- PAGE 1: COVER & OVERVIEW ---
    # Title
    story.append(Paragraph("InsightAI", title_style))
    story.append(Paragraph(f"Executive Sales Analytics & Strategy Report &bull; {report_type.upper()}", subtitle_style))
    
    # Info Block
    generated_str = datetime.now().strftime("%B %d, %Y at %H:%M:%S")
    story.append(Paragraph(f"<b>Generated At:</b> {generated_str}", body_style))
    story.append(Paragraph("<b>Author:</b> InsightAI Business Intelligence Engine", body_style))
    story.append(Spacer(1, 0.2 * inch))

    # Core Stats Table
    total_rev = db.query(func.sum(Sale.revenue)).scalar() or 0.0
    total_prof = db.query(func.sum(Sale.profit)).scalar() or 0.0
    total_orders = db.query(func.count(Sale.sale_id)).scalar() or 0
    total_custs = db.query(func.count(Customer.customer_id)).scalar() or 0
    margin = (total_prof / total_rev * 100) if total_rev > 0 else 0.0
    
    data = [
        ["Key Business Metrics", "Value"],
        ["Total Revenue Generated", f"${total_rev:,.2f}"],
        ["Net Profit Generated", f"${total_prof:,.2f}"],
        ["Net Profit Margin", f"{margin:.2f}%"],
        ["Total Closed Orders", f"{total_orders:,}"],
        ["Active Unique Customers", f"{total_custs:,}"]
    ]
    
    table = Table(data, colWidths=[3.0 * inch, 3.5 * inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#7c3aed")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 11),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#f9fafb")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f3f4f6")]),
        ('TEXTCOLOR', (0,1), (-1,-1), text_color),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 10),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e5e7eb")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    
    story.append(table)
    story.append(Spacer(1, 0.3 * inch))

    # Top Products Table
    story.append(Paragraph("Top Performing Products (Revenue Driver)", h2_style))
    top_prods_query = db.query(
        Product.name, Product.category, func.sum(Sale.revenue).label("rev")
    ).join(Sale).group_by(Product.product_id).order_by(func.sum(Sale.revenue).desc()).limit(4).all()
    
    prod_data = [["Product Name", "Category", "Revenue"]]
    for name, cat, rev in top_prods_query:
        prod_data.append([name, cat, f"${rev:,.2f}"])
        
    prod_table = Table(prod_data, colWidths=[3.5 * inch, 1.5 * inch, 1.5 * inch])
    prod_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4c1d95")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (2,0), (2,-1), 'RIGHT'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e5e7eb")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f9fafb")]),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]))
    story.append(prod_table)
    
    story.append(PageBreak())

    # --- PAGE 2: CHARTS & TRENDS ---
    story.append(Paragraph("Visual Sales Trends", h1_style))
    story.append(Spacer(1, 0.1 * inch))
    
    # Generate Matplotlib chart files
    trend_img, region_img = generate_report_plots(db)
    
    # Embed trend chart
    story.append(Paragraph("<b>Monthly Sales Revenue Growth Trajectory</b>", body_style))
    story.append(Spacer(1, 0.05 * inch))
    story.append(Image(trend_img, width=6.2 * inch, height=2.8 * inch))
    story.append(Spacer(1, 0.2 * inch))

    # Embed region chart
    story.append(Paragraph("<b>Regional Revenue Share Allocation</b>", body_style))
    story.append(Spacer(1, 0.05 * inch))
    story.append(Image(region_img, width=6.2 * inch, height=2.8 * inch))
    
    story.append(PageBreak())

    # --- PAGE 3: AI BUSINESS INSIGHTS ---
    story.append(Paragraph("AI Recommendations & Analytical Insights", h1_style))
    story.append(Spacer(1, 0.1 * inch))
    
    # Parse and append the AI summary paragraphs
    report_paragraphs = convert_markdown_to_pdf_paragraphs(
        markdown_summary,
        body_style,
        bold_body_style,
        h1_style,
        h2_style
    )
    story.extend(report_paragraphs)

    # 3. Build document
    doc.build(story)
    
    # 4. Clean up temporary chart images
    if os.path.exists(trend_img):
        os.remove(trend_img)
    if os.path.exists(region_img):
        os.remove(region_img)
        
    return pdf_path
