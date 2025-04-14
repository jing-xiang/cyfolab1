import hashlib
import os
import email
import pytz
import re
from collections import Counter
from email.utils import getaddresses, parsedate_to_datetime
from email.header import decode_header
from email.policy import default

def sha256_of_file(filename):
    """Computes SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filename, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()

def count_emails(email_dir):
    """Counts the number of .eml files in the directory."""
    if not os.path.exists(email_dir):
        return "Error: Directory does not exist. Extract spam.zip first."
    return len([f for f in os.listdir(email_dir) if f.endswith(".eml")])

def extract_email_address(field):
    """Extracts a clean email address from an email header field."""
    if field:
        decoded_parts = decode_header(field)
        email_addresses = []
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                part = part.decode(encoding or 'utf-8', errors='ignore')
            email_addresses.append(part)
        email_string = "".join(email_addresses)
        if "<" in email_string and ">" in email_string:
            start = email_string.find("<") + 1
            end = email_string.find(">")
            return email_string[start:end].strip().lower()
        else:
            return email_string.strip().lower()
    return None

def decode_header_field(field):
    """Decodes a header field that may have encoded parts."""
    if field:
        dh = decode_header(field)
        decoded = ''
        for part, encoding in dh:
            if isinstance(part, bytes):
                decoded += part.decode(encoding or 'utf-8', errors='ignore')
            else:
                decoded += part
        return decoded
    return ''

def count_unique_senders(folder_path):
    """Counts the number of unique senders in .eml files within a folder."""
    senders = set()
    for filename in os.listdir(folder_path):
        if filename.endswith(".eml"):
            try:
                with open(os.path.join(folder_path, filename), "rb") as f:
                    msg = email.message_from_binary_file(f)
                    sender = extract_email_address(msg.get("From"))
                    if sender:
                        senders.add(sender)
            except Exception as e:
                print(f"Error processing {filename}: {e}")
    return len(senders)

def count_unique_receivers(folder_path):
    """Counts the number of unique receivers in .eml files within a folder."""
    receivers = set()
    for filename in os.listdir(folder_path):
        if filename.endswith(".eml"):
            try:
                with open(os.path.join(folder_path, filename), "rb") as f:
                    msg = email.message_from_binary_file(f)
                    # Get all recipient headers using get_all to capture multiple occurrences
                    recipient_headers = []
                    for header in ["To", "Cc", "Bcc"]:
                        recipient_headers.extend(msg.get_all(header, []))
                    
                    # Process all recipient addresses
                    for header_value in recipient_headers:
                        # Decode the header value first
                        decoded_header = decode_header_field(header_value)
                        # Extract addresses from the decoded header
                        addresses = getaddresses([decoded_header])
                        for name, addr in addresses:
                            if addr:
                                clean_addr = extract_email_address(addr)
                                if clean_addr:
                                    receivers.add(clean_addr)
            except Exception as e:
                print(f"Error processing {filename}: {e}")
    return len(receivers)

def most_likely_country_working_from(folder_path):
    """Finds the most likely country based on email domains."""
    domain_counter = Counter()
    for filename in os.listdir(folder_path):
        if filename.endswith(".eml"):
            try:
                with open(os.path.join(folder_path, filename), "rb") as f:
                    msg = email.message_from_binary_file(f)
                    sender = extract_email_address(msg.get("From"))
                    if sender:
                        domain = sender.split('@')[-1]  # Get the domain part
                        domain_counter[domain] += 1
            except Exception as e:
                print(f"Error processing {filename}: {e}")
    
    # Sort by count and format as comma-separated list
    sorted_domains = sorted(domain_counter.items(), key=lambda x: x[1], reverse=True)
    return ",".join([f"{domain[0][:3]}:{domain[1]}" for domain in sorted_domains])  # Shorten domain names to first 3 chars

def find_earliest_email_date(folder_path):
    """Finds the earliest email date in UTC+0 format."""
    earliest = None
    for filename in os.listdir(folder_path):
        if filename.endswith(".eml"):
            try:
                with open(os.path.join(folder_path, filename), "rb") as f:
                    msg = email.message_from_binary_file(f, policy=default)
                    date_header = msg.get("Date")
                    if date_header:
                        dt = parsedate_to_datetime(date_header)
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=pytz.UTC)
                        else:
                            dt = dt.astimezone(pytz.UTC)
                        if earliest is None or dt < earliest:
                            earliest = dt
            except Exception as e:
                print(f"Error reading {filename}: {e}")
    return earliest.isoformat() if earliest else "No valid email dates found."

def find_latest_email_date(folder_path):
    """Finds the latest email date in UTC+0 format."""
    latest = None
    for filename in os.listdir(folder_path):
        if filename.endswith(".eml"):
            try:
                with open(os.path.join(folder_path, filename), "rb") as f:
                    msg = email.message_from_binary_file(f, policy=default)
                    date_header = msg.get("Date")
                    if date_header:
                        dt = parsedate_to_datetime(date_header)
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=pytz.UTC)
                        else:
                            dt = dt.astimezone(pytz.UTC)
                        if latest is None or dt > latest:
                            latest = dt
            except Exception as e:
                print(f"Error reading {filename}: {e}")
    return latest.isoformat() if latest else "No valid email dates found."

def most_popular_word_plaintext(folder_path):
    """Finds the most popular word in text/plain parts across all emails."""
    word_counter = Counter()
    for filename in os.listdir(folder_path):
        if filename.endswith(".eml"):
            try:
                with open(os.path.join(folder_path, filename), "rb") as f:
                    msg = email.message_from_binary_file(f, policy=default)
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            try:
                                charset = part.get_content_charset() or 'utf-8'
                                payload = part.get_payload(decode=True)
                                if payload:
                                    text = payload.decode(charset, errors='ignore')
                                    words = re.findall(r"\b[a-zA-Z]{2,}\b", text.lower())
                                    word_counter.update(words)
                            except Exception as e:
                                print(f"Error decoding text/plain in {filename}: {e}")
            except Exception as e:
                print(f"Error reading {filename}: {e}")
    return word_counter.most_common(1)[0][0] if word_counter else "No text/plain content found."

def count_attachments(folder_path):
    """Counts the total number of attachments in all emails."""
    attachment_count = 0
    for filename in os.listdir(folder_path):
        if filename.endswith(".eml"):
            try:
                with open(os.path.join(folder_path, filename), "rb") as f:
                    msg = email.message_from_binary_file(f, policy=default)
                    for part in msg.walk():
                        if part.get_content_disposition() == 'attachment':
                            attachment_count += 1
            except Exception as e:
                print(f"Error reading {filename}: {e}")
    return attachment_count

def count_pdf_attachments(folder_path):
    """Counts the total number of PDF attachments in all emails."""
    pdf_count = 0
    for filename in os.listdir(folder_path):
        if filename.endswith(".eml"):
            try:
                with open(os.path.join(folder_path, filename), "rb") as f:
                    msg = email.message_from_binary_file(f, policy=default)
                    for part in msg.walk():
                        if part.get_content_disposition() == 'attachment' and part.get_content_type() == 'application/pdf':
                            pdf_count += 1
            except Exception as e:
                print(f"Error reading {filename}: {e}")
    return pdf_count

def count_image_attachments(folder_path):
    """Counts the total number of image (JPEG/PNG) attachments in all emails."""
    image_count = 0
    for filename in os.listdir(folder_path):
        if filename.endswith(".eml"):
            try:
                with open(os.path.join(folder_path, filename), "rb") as f:
                    msg = email.message_from_binary_file(f, policy=default)
                    for part in msg.walk():
                        if part.get_content_disposition() == 'attachment':
                            content_type = part.get_content_type()
                            if content_type in ["image/jpeg", "image/png"]:
                                image_count += 1
            except Exception as e:
                print(f"Error reading {filename}: {e}")
    return image_count

def count_emails_to_cyfo_inc(folder_path):
    """
    Counts the number of emails sent to CYFO INC.
    An email is considered sent to CYFO INC if any address in its 'To' or 'Cc' headers
    ends with '@cyfoinc.one.com'.
    """
    count = 0
    for filename in os.listdir(folder_path):
        if filename.endswith(".eml"):
            try:
                with open(os.path.join(folder_path, filename), "rb") as f:
                    msg = email.message_from_binary_file(f, policy=default)
                    to_header = msg.get("To", "")
                    cc_header = msg.get("Cc", "")
                    headers = [to_header, cc_header]
                    addresses = getaddresses(headers)
                    for name, addr in addresses:
                        if addr and addr.strip().lower().endswith("@cyfoinc.one.com"):
                            count += 1
                            break  # Count the email only once
            except Exception as e:
                print(f"Error processing {filename}: {e}")
    return count

def count_emails_by_group(folder_path):
    """Counts the number of emails sent by each group based on their domain."""
    group_count = Counter()
    for filename in os.listdir(folder_path):
        if filename.endswith(".eml"):
            try:
                with open(os.path.join(folder_path, filename), "rb") as f:
                    msg = email.message_from_binary_file(f, policy=default)
                    sender = extract_email_address(msg.get("From"))
                    if sender:
                        domain = sender.split('@')[-1]  # Get the domain part
                        group_count[domain] += 1
            except Exception as e:
                print(f"Error processing {filename}: {e}")
    
    # Sort by count and format as comma-separated list
    sorted_groups = sorted(group_count.items(), key=lambda x: x[1], reverse=True)
    return ",".join([f"{group[0][:3]}:{group[1]}" for group in sorted_groups])  # Shorten group names to first 3 chars


# Paths
zip_file = "spam.zip"
email_dir = "spam"  # Ensure this is the correct directory

# Output
print(f"SHA-256 of {zip_file}: {sha256_of_file(zip_file)}")
print(f"Total number of emails: {count_emails(email_dir)}")
print(f"Total number of unique senders: {count_unique_senders(email_dir)}")
print(f"Total number of unique receivers: {count_unique_receivers(email_dir)}")
print(f"Earliest email date (UTC): {find_earliest_email_date(email_dir)}")
print(f"Latest email date (UTC): {find_latest_email_date(email_dir)}")
print(f"Most popular word in text/plain emails: {most_popular_word_plaintext(email_dir)}")
print(f"Total number of attachments: {count_attachments(email_dir)}")
print(f"Total number of PDF attachments: {count_pdf_attachments(email_dir)}")
print(f"Total number of image (JPEG/PNG) attachments: {count_image_attachments(email_dir)}")
print(f"Number of emails sent to CYFO INC: {count_emails_to_cyfo_inc(email_dir)}")
