import pandas as pd
from weasyprint import HTML
import json
import io
from jinja2 import Environment, FileSystemLoader

def generate_pdf(data: dict, template_name: str = "default.html") -> bytes:
    # Render HTML from template (omitted actual template for brevity, using simple string if acceptable or create templates dir)
    # LLD 4.5 -> PDF -> WeasyPrint
    
    html_string = f"""
    <html>
    <head><title>Report {data.get("report_name")}</title></head>
    <body>
        <h1>FactoryOps Report: {data.get("report_name")}</h1>
        <p>Period: {data.get("start")} to {data.get("end")}</p>
        
        <h2>Summary</h2>
        <p>Total Alerts: {len(data.get("alerts", []))}</p>
        
        <h2>Metrics Table</h2>
        {data.get("metrics_html", "<p>No metrics data</p>")}
    </body>
    </html>
    """
    
    pdf_bytes = HTML(string=html_string).write_pdf()
    return pdf_bytes

def generate_excel(metrics_df: pd.DataFrame, alerts_list: list) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        if not metrics_df.empty:
            metrics_df.to_excel(writer, sheet_name='Metrics', index=False)
        
        if alerts_list:
            pd.DataFrame(alerts_list).to_excel(writer, sheet_name='Alerts', index=False)
            
    return buffer.getvalue()

def generate_json(data: dict) -> bytes:
    return json.dumps(data, default=str).encode('utf-8')
