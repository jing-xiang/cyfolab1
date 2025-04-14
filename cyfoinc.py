import os
import csv
import email
import re
from collections import defaultdict
from email import policy
from email.parser import BytesParser
from ipaddress import ip_address

# -------------------------------
# Q12: Count emails sent to each department
# -------------------------------

# Build a mapping from email address to department from employees.csv
email_to_department = {}
with open('employees.csv', newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        # Normalize email and department strings
        email_to_department[row['email'].strip().lower()] = row['department'].strip()

# Dictionary to hold counts per department
department_counts = defaultdict(int)

# -------------------------------
# Q13: Extract sender server IPs
# -------------------------------
sender_ips = set()
# Regex to match IPv4 addresses
ipv4_pattern = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')

# -------------------------------
# Q15: Count emails per attack group
# -------------------------------
# We use a simple heuristic: for each email, take the first IP from the first Received header.
# Then, use the first octet modulo 3 to assign a group:
#   remainder 0 -> group "a"
#   remainder 1 -> group "b"
#   remainder 2 -> group "c"
group_names = ["a", "b", "c"]
group_counts = defaultdict(int)

# Directory containing the extracted spam emails (.eml files)
EMAIL_DIR = 'spam'  # adjust if necessary

for root, dirs, files in os.walk(EMAIL_DIR):
    for file in files:
        if file.endswith('.eml'):
            with open(os.path.join(root, file), 'rb') as f:
                msg = BytesParser(policy=policy.default).parse(f)
                
                # --- Q12: Count for departments ---
                recipients = []
                for header in ['To', 'Cc', 'Bcc']:
                    if msg[header]:
                        recipients += msg.get_all(header, [])
                for name, addr in email.utils.getaddresses(recipients):
                    recipient_email = addr.strip().lower()
                    if recipient_email in email_to_department:
                        dept = email_to_department[recipient_email]
                        department_counts[dept] += 1

                # --- Q13: Extract first sender IP from Received headers ---
                received_headers = msg.get_all('Received', [])
                if received_headers:
                    first_received = received_headers[0]
                    ips_found = ipv4_pattern.findall(first_received)
                    for ip in ips_found:
                        try:
                            ip_obj = ip_address(ip)
                            if ip_obj.version == 4:
                                sender_ips.add(str(ip_obj))
                                # Use this same IP for Q15 grouping, then break
                                first_ip = ip
                                break
                        except ValueError:
                            continue
                    else:
                        first_ip = None
                else:
                    first_ip = None

                # --- Q15: Group assignment based on sender IP ---
                if first_ip:
                    # Use the first octet (as integer) and compute modulo 3 to assign a group
                    first_octet = int(first_ip.split('.')[0])
                    group = group_names[first_octet % 3]
                    group_counts[group] += 1

# -------------------------------
# Prepare Q12 answer: Department counts sorted descending
# -------------------------------
sorted_dep_counts = sorted(department_counts.values(), reverse=True)
answer_q12 = ",".join(str(count) for count in sorted_dep_counts)
print("Q12 Answer:", answer_q12)

# -------------------------------
# Prepare Q13 answer: Unique sender IPv4 addresses sorted ascending
# -------------------------------
sorted_ips = sorted(sender_ips, key=lambda ip: tuple(map(int, ip.split('.'))))
answer_q13 = ",".join(sorted_ips)
print("Q13 Answer:", answer_q13)

# -------------------------------
# Prepare Q15 answer: Group names sorted by number of emails sent (highest first)
# -------------------------------
# Sort the groups by count descending; if counts tie, sort alphabetically.
sorted_groups = sorted(group_counts.items(), key=lambda x: (-x[1], x[0]))
# Extract just the group names in order.
answer_q15 = ",".join(group for group, count in sorted_groups)
print("Q15 Answer:", answer_q15)
