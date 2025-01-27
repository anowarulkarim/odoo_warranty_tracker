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
        print("here")
        product_info = self.action_generate_report_sql()  # Fetch product details
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet()

        # Define formats
        bold_format = workbook.add_format({'bold': True})
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#4CAF50',
            'color': 'white',
            'border': 1
        })
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#FFEB3B',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })
        data_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })
        claim_header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#FF9800',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })

        # Title for the report
        worksheet.merge_range('A1:D1', f"Warranty Report for {self.product_id.name}", title_format)

        # Product Information Table
        worksheet.write('A3', 'Product Details', bold_format)
        product_headers = ['Product Name', 'Serial Number', 'Purchase Date', 'Warranty Start Date',
                           'Warranty End Date', 'Selling Price', 'Days to Expiry', 'Is Expired']

        # Write Product Details table headers
        for col_num, header in enumerate(product_headers):
            worksheet.write(3, col_num, header, header_format)

        # Write the Product Details data (single row for the product)
        for row_num, product in enumerate(product_info, start=4):
            worksheet.write(row_num, 0, product.get('name', 'N/A'), data_format)
            worksheet.write(row_num, 1, product.get('serial_number', 'N/A'), data_format)
            worksheet.write(row_num, 2, str(product.get('purchase_date', 'N/A')), data_format)
            worksheet.write(row_num, 3, str(product.get('warranty_start_date', 'N/A')), data_format)
            worksheet.write(row_num, 4, str(product.get('warranty_end_date', 'N/A')), data_format)
            worksheet.write(row_num, 5, product.get('selling_price', 'N/A'), data_format)
            worksheet.write(row_num, 6, product.get('days_to_expiry', 'N/A'), data_format)
            worksheet.write(row_num, 7, 'Yes' if product.get('is_expired') else 'No', data_format)
            break

        # Add some space between the tables
        claims_start_row = len(product_info) + 5

        # Define Claims Table
        claims_headers = ['Claim ID', 'Claim Date', 'Status', 'Description']

        # Write Claims table headers
        worksheet.write(claims_start_row, 0, 'Warranty Claims', bold_format)
        for col_num, header in enumerate(claims_headers):
            worksheet.write(claims_start_row + 1, col_num, header, claim_header_format)

        # Initialize counters for claim statuses
        claim_status_counts = {'pending': 0, 'approved': 0, 'rejected': 0}

        # Fetch and Write Warranty Claims
        warranty_claims = self.env['warranty.claim'].search([('product_id', '=', self.product_id.id)])
        if warranty_claims:
            for row_num, claim in enumerate(warranty_claims, start=claims_start_row + 2):
                worksheet.write(row_num, 0, claim.id, data_format)
                worksheet.write(row_num, 1, str(claim.claim_date), data_format)
                worksheet.write(row_num, 2, claim.status, data_format)
                worksheet.write(row_num, 3, claim.description, data_format)

                # Count claim statuses
                if claim.status in claim_status_counts:
                    claim_status_counts[claim.status] += 1

        # Prepare chart data
        # Prepare chart data
        chart_data = [
            ['Status', 'Count'],
            ['Pending', claim_status_counts['pending']],
            ['Approved', claim_status_counts['approved']],
            ['Rejected', claim_status_counts['rejected']],
        ]
        print(chart_data)

        # Write chart data into a new range of cells
        chart_data_start_row = len(warranty_claims) + claims_start_row + 4
        worksheet.write_row(f'A{chart_data_start_row}', chart_data[0], bold_format)  # Write headers
        worksheet.write(f'A{chart_data_start_row + 1}', 'Pending', data_format)
        worksheet.write(f'B{chart_data_start_row + 1}', claim_status_counts['pending'], data_format)
        worksheet.write(f'A{chart_data_start_row + 2}', 'Approved', data_format)
        worksheet.write(f'B{chart_data_start_row + 2}', claim_status_counts['approved'], data_format)
        worksheet.write(f'A{chart_data_start_row + 3}', 'Rejected', data_format)
        worksheet.write(f'B{chart_data_start_row + 3}', claim_status_counts['rejected'], data_format)

        # Create the chart
        chart = workbook.add_chart({'type': 'pie'})
        chart.add_series({
            'name': 'Claim Status Distribution',
            'categories': f'A{chart_data_start_row + 1}:A{chart_data_start_row + 3}',
            'values': f'B{chart_data_start_row + 1}:B{chart_data_start_row + 3}',
            'data_labels': {'percentage': True},  # Show percentage labels on the chart
        })
        chart.set_title({'name': 'Claim Status Distribution'})
        chart.set_style(10)

        # Insert the chart into the worksheet
        worksheet.insert_chart(f'E{chart_data_start_row + 1}', chart, {'x_offset': 20, 'y_offset': 20})

        # Create the bar chart
        bar_chart = workbook.add_chart({'type': 'bar'})
        bar_chart.add_series({
            'name': 'Claim Count by Status',
            'categories': f'A{chart_data_start_row + 1}:A{chart_data_start_row + 3}',
            'values': f'B{chart_data_start_row + 1}:B{chart_data_start_row + 3}',
        })
        bar_chart.set_title({'name': 'Claim Count by Status'})
        bar_chart.set_x_axis({'name': 'Status'})
        bar_chart.set_y_axis({'name': 'Count'})
        bar_chart.set_style(11)
        worksheet.insert_chart(f'I{chart_data_start_row + 1}', bar_chart, {'x_offset': 20, 'y_offset': 20})

        # Finalize workbook
        workbook.close()
        output.seek(0)

        # Save file to the transient model
        self.export_file = base64.b64encode(output.read())
        self.file_name = f"{self.product_id.name}_warranty_report.xlsx"
        print(self.export_file)

        return {
            'name': 'Warranty Report',
            'view_mode': 'form',
            'res_id': self.id,
            'res_model': 'warranty.report.wizard',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def product_report(self):
        # html=self.action_generate_report()
        # print(self.action_generate_report_sql())
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