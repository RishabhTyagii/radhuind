"""
Diagnostic tool: sends a standard Tally XML "Export Collection" request to
Tally's local XML/HTTP server and prints the raw response.

Run with:
    python manage.py tally_probe
    python manage.py tally_probe --days 130
    python manage.py tally_probe --from-date 2026-04-01 --to-date 2026-04-01

This does NOT save anything to the database — it's only to see what Tally's
real response looks like, so we can build an accurate parser matching your
actual company's data (item names, ledger names, etc).
"""
import urllib.request
import urllib.error
import datetime
from django.core.management.base import BaseCommand


PROBE_XML = """<ENVELOPE>
  <HEADER>
    <VERSION>1</VERSION>
    <TALLYREQUEST>Export</TALLYREQUEST>
    <TYPE>Collection</TYPE>
    <ID>RadhuVoucherProbe</ID>
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
          <COLLECTION NAME="RadhuVoucherProbe" ISMODIFY="No">
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


class Command(BaseCommand):
    help = "Probe Tally's local XML server and print the raw response (for debugging/mapping only)."

    def add_arguments(self, parser):
        parser.add_argument("--url", default="http://localhost:9000", help="Tally XML server URL")
        parser.add_argument("--days", type=int, default=7, help="How many past days of vouchers to fetch (ignored if --from-date given)")
        parser.add_argument("--from-date", help="Explicit start date, YYYY-MM-DD (overrides --days)")
        parser.add_argument("--to-date", help="Explicit end date, YYYY-MM-DD (defaults to --from-date if only that is given)")

    def handle(self, *args, **options):
        url = options["url"]
        today = datetime.date.today()

        if options["from_date"]:
            from_date = datetime.datetime.strptime(options["from_date"], "%Y-%m-%d").date()
            to_date = (
                datetime.datetime.strptime(options["to_date"], "%Y-%m-%d").date()
                if options["to_date"] else from_date
            )
        else:
            from_date = today - datetime.timedelta(days=options["days"])
            to_date = today

        xml_request = PROBE_XML.format(
            from_date=from_date.strftime("%Y%m%d"),
            to_date=to_date.strftime("%Y%m%d"),
        )

        self.stdout.write(f"Connecting to Tally at {url} ...")
        self.stdout.write(f"Requesting Sales vouchers from {from_date} to {to_date}\n")

        req = urllib.request.Request(
            url,
            data=xml_request.encode("utf-8"),
            headers={"Content-Type": "text/xml; charset=utf-8"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
        except urllib.error.URLError as e:
            self.stderr.write(self.style.ERROR(
                f"Tally se connect nahi ho paaya: {e}\n"
                f"Check karo: (1) Tally Prime khula hai aur company load hai, "
                f"(2) F1 > Settings > Advanced Configuration mein HTTP/XML server 'Yes' hai, "
                f"(3) port {url} sahi hai."
            ))
            return

        if "<VOUCHER" not in raw and "LINEERROR" not in raw:
            self.stdout.write(self.style.WARNING(
                "\nNote: response mein koi <VOUCHER> tag nahi mila — ya to is date range "
                "mein Sales voucher nahi hai, ya company change karni hai (Alt+F3 se check "
                "karo Tally mein sahi company load hai)."
            ))

        self.stdout.write(self.style.SUCCESS("=== RAW TALLY RESPONSE ===\n"))
        self.stdout.write(raw)
        self.stdout.write(self.style.SUCCESS("\n=== END OF RESPONSE ==="))