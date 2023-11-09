from flask import render_template, request, make_response, send_from_directory, flash, redirect, url_for
from flask_paginate import Pagination, get_page_args
from app.CoreB.invoices_list import bp
from app import login_required
from app.models import Invoice
from app import db
from datetime import datetime
from app.pdfwriter import PdfWriter

pdfWriter = PdfWriter("app/static/invoice-base.pdf","app/static/filled-out-v2.pdf")

def list_services(services_str, services_to_find):
    """
    Find what services are requested

    services_str (str): string with services requested
    services_to_find (list(str)): list of possible services to find

    return (list(str)): list of services found 
    """
    services = []

    for service_to_find in services_to_find:
        if services_str.__contains__(service_to_find):
            services.append(service_to_find)
    
    return services

@bp.route('/invoice', methods=['POST'])
@login_required(role=["admin", "coreB"])
def invoice():
    if request.method == 'POST':
        # get order data to input automatically into invoice (passed to POST)
        order_num = request.form.get('order_num')
        acc_num = request.form.get('acc_num')
        # get account number from account field (format: acc_num,additional info)
        acc_num = acc_num.split(",")[0]
        service_type = request.form.get('service_type')
        services_str = request.form.get('services')
        sample_num = request.form.get('sample_num')
        # check what services are selected and put them into array
        services_to_find = ["one", "two", "RNA-seq DEG Analysis", "Pathway Analysis", "Pathway and Pertubagen Analysis", "Variant Calling Analysis"]
        services_data = list_services(services_str, services_to_find)

        # pass dict with hidden data just to pass it to the next request
        hidden_data = {
            "Account Number": acc_num,
            "Quantity" : sample_num,
            "Order Number": order_num
        }

        # get invoice data from DB for each service or make arecord if none exists
        invoices = []
        for service_data in services_data:
            invoice = Invoice.query.filter_by(project_id = order_num, service_type=service_data).first()
            if invoice == None:
                invoice = Invoice(project_id = order_num, 
                                service_type = service_data,
                                service_sample_number = 0.0,
                                service_sample_price = 0.0, 
                                total_price = 0.0,
                                discount_sample_number = 0.0,
                                discount_sample_amount = 0.0,
                                discount_reason = "", 
                                total_discount = 0.0)
                db.session.add(invoice)
            invoices.append(invoice)

        invoice = Invoice.query.filter_by(project_id = order_num, service_type="All services discount").first()
        if invoice == None:
            invoice = Invoice(project_id = order_num, 
                            service_type = "All services discount",
                            service_sample_number = 0.0,
                            service_sample_price = 0.0, 
                            total_price = 0.0,
                            discount_sample_number = 0.0,
                            discount_sample_amount = 0.0,
                            discount_reason = "", 
                            total_discount = 0.0)
            
            db.session.add(invoice)
        invoices.append(invoice)
        db.session.commit()

        return render_template('edit_invoice.html', order_num = order_num, service_type = service_type, sample_num = sample_num, fields_hidden = hidden_data, invoices=invoices, len=len)

@bp.route('/gen_invoice', methods=['POST'])
@login_required(role=["admin", "coreB"])
def gen_invoice(): 
    if request.method == 'POST':
        # get order data to input automatically into invoice
        order_num = request.form.get("Order Number") or ""
        acc_num = request.form.get('Account Number') or ""
        services_num = request.form.get('Services Number') or 0

        # based on order data prepare inputs
        date = datetime.now().strftime('%m/%d/%Y')

        dict_data = {
            'DEBIT ACCOUNTRow1': acc_num,
            'DEPT REQUISITION Row1': order_num,
            'Date5_af_date': date
        }

        # services details
        # initial row number values to start from
        service_row = 3
        item_number = 1
        # initial grand total prices
        grand_total_discount = 0.0
        grand_total = 0.0
        total_service_amount = 0.0
        # loop all services
        for i in range(0, int(services_num)):
            # get needed values from invoice form
            get_name_key = "service " + str(i) + " name"
            get_qty_key = "service " + str(i) + " qty"
            get_discount_reason_key = "service " + str(i) + " discount reason"
            get_discount_qty_key = "service " + str(i) + " discount qty"
            get_discount_amount_key = "service " + str(i) + " discount amount"
            service_price_key = "service " + str(i) + " price"
            service_name_detail = request.form.get(get_name_key)
            service_qty_detail = request.form.get(get_qty_key)
            service_discount_reason_detail = request.form.get(get_discount_reason_key)
            service_discount_qty_detail = request.form.get(get_discount_qty_key)
            service_discount_amount_detail = request.form.get(get_discount_amount_key)
            service_price_detail = request.form.get(service_price_key)

            if service_name_detail == "All services discount":
                service_row = 21

            # Discount details keys
            item_discount_key = "ITEM Row" + str(service_row + 1)
            qty_discount_key = "QTYRow" + str(service_row + 1)
            unit_discount_key = "UNITRow" + str(service_row + 1)
            service_discount_reason_key = "DESCRIPTIONRow" + str(service_row + 1)
            service_discount_amount_key = "UNIT COSTRow" + str(service_row + 1)
            service_discount_total_key = "TOTALRow" + str(service_row + 1)

            if service_name_detail != "All services discount":
                # Service details keys
                item_key = "ITEM Row" + str(service_row)
                qty_key = "QTYRow" + str(service_row)
                unit_key = "UNITRow" + str(service_row)
                service_name_key = "DESCRIPTIONRow" + str(service_row)
                service_amount_key = "UNIT COSTRow" + str(service_row)
                service_total_key = "TOTALRow" + str(service_row)

                # Service details values
                if service_price_detail == "":
                    return render_template('error_invoice.html', error_msg="Service price must be provided")
                elif service_qty_detail == "":
                    return render_template('error_invoice.html', error_msg="Service samples must be provided")
            
                service_price_detail = float(service_price_detail)
                dict_data[item_key] = str(item_number)
                dict_data[qty_key] = service_qty_detail
                dict_data[unit_key] = "ea"
                dict_data[service_name_key] = service_name_detail
                dict_data[service_amount_key] = str(service_price_detail) + " $"
                total_service_amount = float(service_qty_detail) * service_price_detail
                grand_total += total_service_amount
                dict_data[service_total_key] = str(total_service_amount) + " $"

            # var to insert total discount amount to DB
            total_discount_amount = 0.0

            # Discount details values
            if service_discount_reason_detail != None and len(service_discount_reason_detail) != 0:
                if service_discount_amount_detail == "":
                    return render_template('error_invoice.html', error_msg="Discount amount must be provided")
                elif service_discount_qty_detail == "":
                    return render_template('error_invoice.html', error_msg="Discounted sample number must be provided")
                service_discount_amount_detail = float(service_discount_amount_detail)
                dict_data[item_discount_key] = str(item_number+1)
                dict_data[qty_discount_key] = service_discount_qty_detail
                dict_data[unit_discount_key] = "ea"
                dict_data[service_discount_reason_key] = service_discount_reason_detail
                dict_data[service_discount_amount_key] = str(-service_discount_amount_detail) + " $"
                if service_name_detail == "All services discount":
                    service_discount_qty_detail = 1.0
                    total_service_amount = 0.0
                total_discount_amount = float(service_discount_qty_detail) * service_discount_amount_detail
                grand_total_discount += total_discount_amount
                dict_data[service_discount_total_key] = str(-total_discount_amount) + " $"

            # change values of invoice record
            existing_invoice = Invoice.query.filter_by(project_id = order_num, service_type = service_name_detail).first()

            existing_invoice.service_sample_number = float(service_qty_detail)
            existing_invoice.service_sample_price = service_price_detail
            existing_invoice.total_price = total_service_amount
            existing_invoice.discount_sample_number = float(service_discount_qty_detail)
            existing_invoice.discount_sample_amount = service_discount_amount_detail
            existing_invoice.discount_reason = service_discount_reason_detail
            existing_invoice.total_discount = total_discount_amount
            db.session.commit()


            # increment row to put data info into
            service_row += 2
            item_number += 2

        # grand total price of service
        service_grand_total_key = "TOTALGRAND TOTAL"
        dict_data[service_grand_total_key] = str(grand_total - grand_total_discount) + " $"

        pdfWriter.fillForm(dict_data)
        return send_from_directory('static', "filled-out-v2.pdf")

@bp.route('/invoices_list', methods=['GET', 'POST'])
@login_required(role=["admin"])
def invoices_list():
    # get invoice list data
    invoices = Invoice.query.all()
    data = []

    for invoice in invoices:
        invoice_dict = {}
        invoice_dict["Project ID"] = invoice.project_id
        invoice_dict["Service type"] = invoice.service_type
        invoice_dict["Total price"] = invoice.total_price
        invoice_dict["Total discount"] = invoice.total_discount
        invoice_dict["Final price"] = float(invoice.total_price) - float(invoice.total_discount)
        data.append(invoice_dict)

    if request.method == 'POST':
        # search vars
        service_type = request.form.get('service_type') or ""
        # filter dict
        data = [dict for dict in data if dict['Service type'].lower().__contains__(service_type.lower())]
        sort = request.form.get('sort') or "Original"
        # sort dict
        if sort != 'Original':
            data = sorted(data, key=lambda d: d[sort])

        # TODO error while data empty, show diff screen

    page, per_page, offset = get_page_args(page_parameter='page', 
                                        per_page_parameter='per_page')
    total = len(data)

    pagination_users = data[offset: offset + per_page]
    pagination = Pagination(page=page, per_page=per_page, total=total)

    # use to prevent user from caching pages
    response = make_response(render_template("invoices_list.html", data=pagination_users, page=page, per_page=per_page, pagination=pagination, list=list, len=len, str=str))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
    response.headers["Pragma"] = "no-cache" # HTTP 1.0.
    response.headers["Expires"] = "0" # Proxies.
    return response

    #return render_template("invoices_list.html", data=pagination_users, page=page, per_page=per_page, pagination=pagination, list=list, len=len, str=str)