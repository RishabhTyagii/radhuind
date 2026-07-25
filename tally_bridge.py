"""
tally_bridge.py
----------------
Runs on the SAME PC as Tally. Pulls Sales vouchers from Tally's local
XML/HTTP interface (default port 9000) and pushes them to the Django
tallysync webhook, in the JSON shape views.tally_webhook() expects.

Field mapping below was CONFIRMED against a real probe response from
this Tally company (see tally_probe.py output), so tag names should
match as-is. If you add new GST ledgers, non-Sales voucher types, etc.,
re-run the probe and adjust parse_vouchers() if needed.

SETUP
1. Tally's HTTP/XML server must be on (already confirmed working -
   port 9000 responds).
2. Test parsing only, no push:
       python tally_bridge.py --from-date 2026-04-01 --to-date 2026-04-01 --dry-run
3. Once the printed summary looks right, push for real:
       python tally_bridge.py --from-date 2026-04-01 --to-date 2026-04-01
   Then check the Django Sales & GST Summary page for that month - the
   invoices should now appear.
4. For ongoing/day-to-day use:
       python tally_bridge.py --loop --interval 300
   This re-checks Tally every 5 minutes for TODAY's date and pushes
   any new vouchers. Schedule it with Windows Task Scheduler so it
   restarts automatically after a reboot.

IMPORTANT: unmapped items
If a Tally item name (e.g. "90/100/18 Tl Attack") has no matching row
in Item Mapping (tallysync/mapping/add/), the invoice will still show
up in the Sales & GST Summary — but its stock WON'T be reduced, and a
warning will appear in the Sync Log. Map every item first via the
"+ New Mapping" page.
"""

import argparse
import datetime
import re
import time
import xml.etree.ElementTree as ET

import requests


def _sanitize_xml(text):
    """Tally emits invalid XML control-character references like '&#4;'
    (e.g. inside INDENTNO/ORDERNO/TRACKINGNUMBER as a placeholder for
    'Not Applicable'). These are illegal in XML 1.0 and make Python's
    parser raise ParseError. Strip only the illegal ones; leave valid
    character references (tab/newline/CR and normal printable chars)
    untouched."""
    def repl(m):
        code = int(m.group(1))
        if code in (9, 10, 13) or code >= 32:
            return m.group(0)
        return ""
    return re.sub(r"&#(\d+);", repl, text)

# ---- CONFIG: adjust if your setup differs -------------------------------
TALLY_URL = "http://localhost:9000"
WEBHOOK_URL = "http://127.0.0.1:8000/tallysync/webhook/"
API_KEY = "fc2e1029465c118d144c93a093c0efd2cfa2d40a258c32c8"
# ---------------------------------------------------------------------------

PROBE_XML = """<ENVELOPE>
  <HEADER>
    <VERSION>1</VERSION>
    <TALLYREQUEST>Export</TALLYREQUEST>
    <TYPE>Collection</TYPE>
    <ID>RadhuVoucherBridge</ID>
  </HEADER>
  <BODY>
    <DESC>
      <STATICVARIABLES>
        <SVFROMDATE>{from_date}</SVFROMDATE>
        <SVTODATE>{to_date}</SVTODATE>
        <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
      </STATICVARIABLES>
      <TDL>
        <TDLMESSAGE>
          <COLLECTION NAME="RadhuVoucherBridge" ISMODIFY="No">
            <TYPE>Voucher</TYPE>
            <FETCH>Date, VoucherNumber, VoucherTypeName, PartyLedgerName, Amount, AllLedgerEntries.LedgerName, AllLedgerEntries.Amount, AllInventoryEntries.StockItemName, AllInventoryEntries.ActualQty, AllInventoryEntries.Rate, AllInventoryEntries.Amount</FETCH>
            <FILTER>RadhuOnlySales</FILTER>
          </COLLECTION>
          <SYSTEM TYPE="Formulae" NAME="RadhuOnlySales">$VoucherTypeName = "Sales"</SYSTEM>
        </TDLMESSAGE>
      </TDL>
    </DESC>
  </BODY>
</ENVELOPE>"""


def fetch_vouchers_xml(from_date, to_date):
    """from_date/to_date: 'YYYYMMDD' strings. Returns raw XML text from Tally."""
    xml_request = PROBE_XML.format(from_date=from_date, to_date=to_date)
    resp = requests.post(
        TALLY_URL,
        data=xml_request.encode("utf-8"),
        headers={"Content-Type": "text/xml; charset=utf-8"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.text


def _txt(el, path, default=""):
    found = el.find(path)
    return found.text.strip() if found is not None and found.text else default


def _amount(s):
    try:
        return abs(float(str(s).replace(",", "") or 0))
    except ValueError:
        return 0.0


def parse_vouchers(xml_text):
    """Turn raw Voucher-collection XML into a list of dicts matching the
    webhook's expected JSON shape."""
    root = ET.fromstring(_sanitize_xml(xml_text))
    vouchers = []

    for v in root.iter("VOUCHER"):
        vtype = _txt(v, "VOUCHERTYPENAME")
        if "sales" not in vtype.lower():
            continue

        voucher_number = _txt(v, "VOUCHERNUMBER")
        date_raw = _txt(v, "DATE")  # YYYYMMDD
        try:
            voucher_date = datetime.datetime.strptime(date_raw, "%Y%m%d").strftime("%Y-%m-%d")
        except ValueError:
            voucher_date = datetime.date.today().isoformat()
        party_name = _txt(v, "PARTYLEDGERNAME")

        taxable_value = 0.0
        cgst = sgst = igst = 0.0
        total_value = _amount(_txt(v, "AMOUNT"))

        # ALLLEDGERENTRIES.LIST carries the GST + sales-ledger amounts
        for ledger in v.iter("ALLLEDGERENTRIES.LIST"):
            lname = _txt(ledger, "LEDGERNAME").lower()
            amt = _amount(_txt(ledger, "AMOUNT"))
            if "cgst" in lname:
                cgst += amt
            elif "sgst" in lname:
                sgst += amt
            elif "igst" in lname:
                igst += amt
            elif "sales" in lname:
                taxable_value += amt

        if not taxable_value:
            taxable_value = max(total_value - cgst - sgst - igst, 0)

        # ALLINVENTORYENTRIES.LIST carries the item lines
        items = []
        for inv_entry in v.iter("ALLINVENTORYENTRIES.LIST"):
            item_name = _txt(inv_entry, "STOCKITEMNAME")
            qty_raw = _txt(inv_entry, "ACTUALQTY") or _txt(inv_entry, "BILLEDQTY")  # e.g. "100 pcs"
            qty_num = "".join(ch for ch in qty_raw.split(" ")[0] if (ch.isdigit() or ch == "."))
            try:
                qty = int(float(qty_num or 0))
            except ValueError:
                qty = 0
            amount = _amount(_txt(inv_entry, "AMOUNT"))
            if item_name:
                items.append({"name": item_name, "qty": qty, "amount": amount})

        vouchers.append({
            "voucher_number": voucher_number,
            "date": voucher_date,
            "party_name": party_name,
            "taxable_value": round(taxable_value, 2),
            "cgst": round(cgst, 2),
            "sgst": round(sgst, 2),
            "igst": round(igst, 2),
            "total_value": round(total_value, 2),
            "items": items,
        })

    return vouchers


def push_to_webhook(payload):
    headers = {"X-API-KEY": API_KEY, "Content-Type": "application/json"}
    resp = requests.post(WEBHOOK_URL, json=payload, headers=headers, timeout=15)
    return resp.status_code, resp.text


def sync_once(from_date, to_date, dry_run=False):
    xml_text = fetch_vouchers_xml(from_date, to_date)
    vouchers = parse_vouchers(xml_text)
    print(f"[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] {len(vouchers)} Sales voucher(s) found in Tally.")

    for v in vouchers:
        print(f"  {v['voucher_number']} | {v['party_name']} | items={[i['name'] for i in v['items']]} "
              f"| taxable={v['taxable_value']} cgst={v['cgst']} sgst={v['sgst']} igst={v['igst']} total={v['total_value']}")
        if dry_run:
            continue
        status, body = push_to_webhook(v)
        print(f"    -> HTTP {status} | {body[:200]}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="Single date to sync, YYYY-MM-DD (default: today)")
    parser.add_argument("--from-date", help="Range start, YYYY-MM-DD")
    parser.add_argument("--to-date", help="Range end, YYYY-MM-DD")
    parser.add_argument("--dry-run", action="store_true", help="Parse and print, but don't POST to webhook")
    parser.add_argument("--loop", action="store_true", help="Keep running, re-sync every --interval seconds (uses today's date)")
    parser.add_argument("--interval", type=int, default=300, help="Seconds between syncs in --loop mode")
    args = parser.parse_args()

    today = datetime.date.today()
    if args.date:
        d = datetime.datetime.strptime(args.date, "%Y-%m-%d").date()
        from_date = to_date = d
    elif args.from_date and args.to_date:
        from_date = datetime.datetime.strptime(args.from_date, "%Y-%m-%d").date()
        to_date = datetime.datetime.strptime(args.to_date, "%Y-%m-%d").date()
    else:
        from_date = to_date = today

    if args.loop:
        print(f"Looping every {args.interval}s (syncing today's vouchers). Ctrl+C to stop.")
        while True:
            try:
                today = datetime.date.today()
                sync_once(today.strftime("%Y%m%d"), today.strftime("%Y%m%d"), dry_run=args.dry_run)
            except Exception as e:
                print("Sync error:", e)
            time.sleep(args.interval)
    else:
        sync_once(from_date.strftime("%Y%m%d"), to_date.strftime("%Y%m%d"), dry_run=args.dry_run)


if __name__ == "__main__":
    main()