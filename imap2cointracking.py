import imaplib
import email
import re
import csv
from datetime import datetime
import json
from email.header import decode_header
from email.utils import parsedate_to_datetime


# Konfigurationsdatei
SECRETS_FILE    = 'c:/secrets/imap.json' # TODO
MAIL_FROM       = 'Goldsparplan@degussa-goldhandel.de'
MAIL_SUBJECT    = "Kaufbestätigung Degussa Goldsparplan" # "'=?utf-8?B?S2F1ZmJlc3TDpHRpZ3VuZyBEZWd1c3NhIEdvbGRzcGFycGxh?=\r\n =?utf-8?B?bg==?='" # "Kaufbestätigung Degussa Goldsparplan"

CT_EXCHANGE     = "reallife"
CT_TRADEGROUP   = "Gold"

CSV_DELIMITER   = ";" # semicolon for german CSV, change to comma "," for international
FLOAT_DIVIDER   = "," # comma for german floats, change to "." for international
SF_CSV_INT      = 'goldsparplan_daten_INT.csv' # temp csv for transactions
SF_CSV_GER      = 'goldsparplan_daten_GER.csv' # for german excel
SF_CSV_CT       = 'goldsparplan_daten_CT.csv' # output file for cointracking import

def main():
    # imap2csv()
    csv_2_ct_import(SF_CSV_INT, SF_CSV_CT)

def csv_2_ct_import(csv_in, csv_out):
    """Konvertiert eine CSV-Datei in das CoinTracking-Importformat."""
    print("READ: "+csv_in)
    with open(csv_in, 'r', newline='') as infile:
        reader = csv.DictReader(infile, delimiter=',')

        # Definiere die Header für CoinTracking
        fieldnames = ["Type", "Buy Amount", "Buy Currency", "Sell Amount", "Sell Currency", "Fee", "Fee Currency", "Exchange", "Trade-Group", "Comment", "Date", "Tx-ID", "Buy Value in Account Currency"]

        with open(csv_out, 'w', newline='') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter=',')
            writer.writeheader()

            for row in reader:
                # Erstelle ein Dictionary für CoinTracking

                ct_row_1_fiat_source = {
                    "Type": "Einzahlung",  # Annahme: Alle Transaktionen sind Käufe
                    "Buy Amount": float(row['EURO']), # Konvertiere Euro in Float
                    "Buy Currency": "EUR",
                    "Sell Amount": "",
                    "Sell Currency": "",
                    "Fee": 0.0,
                    "Fee Currency": "",
                    "Exchange": CT_EXCHANGE,  # Annahme: Degussa als Exchange
                    "Trade-Group": CT_TRADEGROUP,
                    "Comment": f"Degussa Dummy-Einzahlung Kruegerrand",
                    "Date": row['DATUM_CT'], # Verwende das Datum im CoinTracking-Format
                    "Tx-ID": "Pre-"+re.sub(r'[^a-zA-Z0-9]', '_', row['ID']),
                    "Buy Value in Account Currency": float(row['EURO'])
                }
                writer.writerow(ct_row_1_fiat_source)
                
                ct_row_2_trade = {
                    "Type": "Trade",  # Annahme: Alle Transaktionen sind Käufe
                    "Buy Amount": float(row['ANTEILE']), # Konvertiere Euro in Float
                    "Buy Currency": "XAU",
                    "Sell Amount": float(row['EURO']),
                    "Sell Currency": "EUR",
                    "Fee": 0.0,
                    "Fee Currency": "",
                    "Exchange": CT_EXCHANGE,  # Annahme: Degussa als Exchange
                    "Trade-Group": CT_TRADEGROUP,
                    "Comment": f"Degussa balance: {row['BALANCE_OZ']} oz Kruegerrand",
                    "Date": row['DATUM_CT'], # Verwende das Datum im CoinTracking-Format
                    "Tx-ID": re.sub(r'[^a-zA-Z0-9]', '_', row['ID']),
                    "Buy Value in Account Currency": float(row['EURO'])
                }
                writer.writerow(ct_row_2_trade)
            print("WRITE: "+csv_out)


def load_config():
    """Lädt die Konfigurationsdaten aus der JSON-Datei."""
    try:
        with open(SECRETS_FILE, 'r') as f:
            config = json.load(f)
            return config
    except FileNotFoundError:
        print("Konfigurationsdatei nicht gefunden.")
        return None
    except json.JSONDecodeError:
        print("Fehler beim Parsen der Konfigurationsdatei.")
        return None
    print("Loaded config file: "+SECRETS_FILE)

def extract_data(text):
    """Extrahiert Daten aus dem E-Mail-Text."""
    try:
        # euro = float(re.search(r"(\d+,\d{2})\s*€", text).group(1))
        euro_str = re.search(r"(\d+,\d{2})\s*€", text).group(1)
        euro = float(euro_str.replace(',', '.'))

        anteile_str = re.search(r"([\d.,]+)\s*Anteile", text).group(1)
        anteile = float(anteile_str.replace(',', '.'))

        balance_oz_str = re.search(r"([\d.,]+)\s*Stück\s*angewachsen", text).group(1)
        balance_oz = float(balance_oz_str.replace(',', '.'))

        goldpreis_str = re.search(r"([\d\.]+,\d{2})\s*€\s*je\s*Stück", text).group(1)
        goldpreis = float(goldpreis_str.replace(',', '.'))
        #datum_string = datetime.now().strftime("%Y-%m-%d") # Da kein Datum im Text gefunden wurde, wird das aktuelle Datum verwendet
        return {"EURO": euro, "ANTEILE": anteile, "GOLDPREIS": goldpreis, "BALANCE_OZ": balance_oz}
    except AttributeError:
        print("Daten konnten nicht extrahiert werden. E-Mail-Format möglicherweise unerwartet.")
        return None

def imap2csv():
    """Hauptfunktion zum Abrufen und Verarbeiten von E-Mails."""
    config = load_config()
    if not config:
        return

    IMAP_SERVER = config['imap_server']
    IMAP_PORT = config['imap_port']
    USERNAME = config['username']
    PASSWORD = config['password']
    EMAIL_ADDRESS = config['email_address']

    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(USERNAME, PASSWORD)
        mail.select('inbox')  # Oder einen anderen Ordner, falls erforderlich

        status, searchresponse = mail.search(None, 'FROM', MAIL_FROM)
        messages = searchresponse[0].split()
        print(f"{IMAP_SERVER} lieferte {len(messages)} Nachrichten von {MAIL_FROM}.")

        data_list = []
        for msg_id in messages:
            status, msg_data = mail.fetch(msg_id, '(RFC822)')
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    raw_email = response_part[1]
                    msg = email.message_from_bytes(raw_email)                    

                    date_header = msg['Date']
                    date_object = parsedate_to_datetime(date_header)

                    msg_id = msg['Message-ID']

                    s_date_ct=date_object.strftime("%Y%m%d%H%M%S")
                    s_date_human=date_object.strftime("%Y-%m-%d %H:%M:%S")
                    # CoinTracking erwartet das Format YYYYMMDDHHMMSS

                    # subject_raw = msg.get('Subject', '')
                    subject = decode_subject(msg.get('Subject', ''))                       
                    if not subject==MAIL_SUBJECT:
                        continue

                    text = None
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            content_disposition = str(part.get("Content-Disposition"))

                            if content_type == "text/plain" and "attachment" not in content_disposition:
                                payload = part.get_payload(decode=True)
                                charset = part.get_content_charset() or "utf-8"
                                if payload:
                                    text = payload.decode(charset, errors="replace")
                                    break  # Nur den ersten brauchbaren Text nehmen
                    else:
                        payload = msg.get_payload(decode=True)
                        charset = msg.get_content_charset() or "utf-8"
                        if payload:
                            text = payload.decode(charset, errors="replace")

                    if text:
                        extracted_data = extract_data(text)
                        if extracted_data:
                            extracted_data['DATUM'] = s_date_human
                            extracted_data['DATUM_CT'] = s_date_ct
                            extracted_data['ID'] = msg_id
                            data_list.append(extracted_data)
        print(f"{len(data_list)} Datensätze extrahiert mt Betreff '{MAIL_SUBJECT}'")
        mail.close()
        mail.logout()

    except imaplib.IMAP4.error as e:
        print(f"Fehler beim Verbinden mit dem IMAP-Server oder Anmelden: {e}")
        return


    # CSV-Ausgabe
    if data_list:
        csv_file = SF_CSV_INT
        fieldnames = ['DATUM', 'EURO', 'ANTEILE', 'GOLDPREIS', 'DATUM_CT', "ID", "BALANCE_OZ"]  # Reihenfolge der Spalten in der CSV-Datei
        with open(csv_file, 'w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=",")
            writer.writeheader()
            writer.writerows(data_list)

        print(f"Daten erfolgreich in {csv_file} gespeichert.")

        csv_file = 'goldsparplan_daten_GER.csv'
        fieldnames = ['DATUM', 'EURO', 'ANTEILE', 'GOLDPREIS', 'DATUM_CT', "ID", "BALANCE_OZ"]  # Reihenfolge der Spalten in der CSV-Datei
        with open(csv_file, 'w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=CSV_DELIMITER)
            writer.writeheader()

            # writer.writerows(data_list)
            for row in data_list:
                # Ersetze Punkte durch Kommas in numerischen Werten
                row['EURO']         = str(row['EURO']       ).replace('.', FLOAT_DIVIDER)
                row['ANTEILE']      = str(row['ANTEILE']    ).replace('.', FLOAT_DIVIDER)
                row['GOLDPREIS']    = str(row['GOLDPREIS']  ).replace('.', FLOAT_DIVIDER)
                row['BALANCE_OZ']   = str(row['BALANCE_OZ'] ).replace('.', FLOAT_DIVIDER)
                # row['DATUM_CT']   = str(row['DATUM_CT']   )

                writer.writerow(row)

        print(f"Daten erfolgreich in {csv_file} gespeichert.")
    else:
        print("Keine Daten gefunden oder extrahiert.")

def decode_subject(subject_raw):
    decoded_parts = decode_header(subject_raw)
    subject = ''
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            try:
                subject += part.decode(encoding or 'utf-8', errors='replace')
            except LookupError:
                subject += part.decode('utf-8', errors='replace')
        else:
            subject += part
    return subject


if __name__ == "__main__":
    main()
