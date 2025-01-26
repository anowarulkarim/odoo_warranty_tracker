from odoo import models, fields, api, _
import base64
import io
import xlsxwriter

class WarrantyReportWizard(models.TransientModel):
    _name = 'warranty.report.wizard'
    _description = 'Warranty Report Wizard'

    product_id = fields.Many2one('warranty.product', string='Product')
    preview = fields.Html(string='Preview', readonly=True)
    export_file = fields.Binary(string='Export File', readonly=True)
    file_name = fields.Char(string='File Name', size=64)


    def report_exl(self):
        product_info=self.action_generate_report_sql()
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet()

        # Define the headers
        headers = ['Claim ID', 'Claim Date', 'Status', 'Description']
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header)

        # Write the data
        for row_num, claim in enumerate(product_info, start=1):
            worksheet.write(row_num, 0, claim['id'])
            worksheet.write(row_num, 1, claim['claim_date'])
            worksheet.write(row_num, 2, claim['status'])
            worksheet.write(row_num, 3, claim['description'])

        workbook.close()
        output.seek(0)
        self.export_file = base64.b64encode(output.read())
        self.file_name = f"{self.product_id.name}_warranty_report.xlsx"


    def product_report(self):
        # html=self.action_generate_report()
        print(self.action_generate_report_sql())
        prodct_info=self.action_generate_report_sql()
        table="<table border='1'>"
        table += f"""
        <tr style="background-color: #007bff; color: #ffffff; text-transform: uppercase; font-size: 14px; font-weight: bold;">
            <th style="padding: 12px 15px; text-align: left;">Claim ID</th>
            <th style="padding: 12px 15px; text-align: left;">Claim Date</th>
            <th style="padding: 12px 15px; text-align: left;">Status</th>
            <th style="padding: 12px 15px; text-align: left;">Description</th>
        </tr>
        """
        table +=  f"""
        <tr style="background-color: #f9f9f9;">
            <th style="padding: 12px 15px; text-align: left;">Product</th>
            <td style="padding: 12px 15px; text-align: left;">{self.product_id.name}</td>
        </tr>
        <tr style="background-color: #ffffff;">
            <th style="padding: 12px 15px; text-align: left;">Warranty Start Date</th>
            <td style="padding: 12px 15px; text-align: left;">{self.product_id.warranty_start_date}</td>
        </tr>
        <tr style="background-color: #f9f9f9;">
            <th style="padding: 12px 15px; text-align: left;">Warranty End Date</th>
            <td style="padding: 12px 15px; text-align: left;">{self.product_id.warranty_end_date}</td>
        </tr>
        <tr style="background-color: #ffffff;">
            <th style="padding: 12px 15px; text-align: left;">Is Expired</th>
            <td style="padding: 12px 15px; text-align: left; font-weight: bold; color: #d9534f;">{'Yes' if self.product_id.is_expired else 'No'}</td>
        </tr>
        <tr style="background-color: #f9f9f9;">
            <th style="padding: 12px 15px; text-align: left;">Days to Expiry</th>
            <td style="padding: 12px 15px; text-align: left;">{self.product_id.days_to_expiry}</td>
        </tr>
        <tr style="background-color: #ffffff;">
            <th style="padding: 12px 15px; text-align: left;">Warranty Duration</th>
            <td style="padding: 12px 15px; text-align: left;">{self.product_id.warranty_duration}</td>
        </tr>
        """
        for claim in prodct_info:
            table += "<tr>"
            table += f"<td>{claim['id']}</td>"
            table += f"<td>{claim['claim_date']}</td>"
            table += f"<td>{claim['status']}</td>"
            table += f"<td>{claim['description']}</td>"
            table += "</tr>"
        table += "</table>"
        html = table

        if html:
            self.write({'preview': html})


    def report_clear(self):
        self.write({'preview': ''})

    def action_generate_report_sql(self):
        if not self.product_id:
            print("No product selected")
            return
        else:
            product = self.product_id
            query = """
                SELECT wp.*, wc.*
                FROM warranty_product AS wp
                INNER JOIN warranty_claim AS wc ON wp.id = wc.product_id
                WHERE wp.id = %s
            """ % (product.id,)
            self.env.cr.execute(query)
            result = self.env.cr.dictfetchall()
            

            return result    

    def action_generate_report(self):
        if not self.product_id:
            print("No product selected")
            return
        else:
            
            product = self.product_id
            html = f"""
<table style="
    width: 100%;
    border-collapse: collapse;
    font-family: Arial, sans-serif;
    margin: 20px 0;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
">
    <tr style="background-color: #007bff; color: #ffffff; text-transform: uppercase; font-size: 14px; font-weight: bold;">
        <th style="padding: 12px 15px; text-align: left;">Product</th>
        <td style="padding: 12px 15px; text-align: left;">{product.name}</td>
    </tr>
    <tr style="background-color: #f9f9f9;">
        <th style="padding: 12px 15px; text-align: left;">Warranty Start Date</th>
        <td style="padding: 12px 15px; text-align: left;">{product.warranty_start_date}</td>
    </tr>
    <tr style="background-color: #ffffff;">
        <th style="padding: 12px 15px; text-align: left;">Warranty End Date</th>
        <td style="padding: 12px 15px; text-align: left;">{product.warranty_end_date}</td>
    </tr>
    <tr style="background-color: #f9f9f9;">
        <th style="padding: 12px 15px; text-align: left;">Is Expired</th>
        <td style="padding: 12px 15px; text-align: left; font-weight: bold; color: #d9534f;">{'Yes' if product.is_expired else 'No'}</td>
    </tr>
    <tr style="background-color: #ffffff;">
        <th style="padding: 12px 15px; text-align: left;">Days to Expiry</th>
        <td style="padding: 12px 15px; text-align: left;">{product.days_to_expiry}</td>
    </tr>
    <tr style="background-color: #f9f9f9;">
        <th style="padding: 12px 15px; text-align: left;">Warranty Duration</th>
        <td style="padding: 12px 15px; text-align: left;">{product.warranty_duration}</td>
    </tr>
</table>
"""

            return html
        