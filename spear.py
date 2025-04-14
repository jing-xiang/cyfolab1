import os
import re
from collections import defaultdict
from email.utils import parsedate_to_datetime
from datetime import datetime

def extract_received_servers(eml_path):
    with open(eml_path, 'r', errors='ignore') as f:
        content = f.read()
        received = re.findall(r'Received:.*?from\s+([^\s;]+)', content, re.IGNORECASE)
        return received[0] if received else None

def parse_date(eml_path):
    with open(eml_path, 'r', errors='ignore') as f:
        content = f.read()
        date_match = re.search(r'Date: (.+)', content, re.IGNORECASE)
        if date_match:
            try:
                return parsedate_to_datetime(date_match.group(1))
            except:
                return None
    return None

def is_working_hours(dt):
    if not dt: return False
    local = dt.astimezone(dt.tzinfo)
    return local.weekday() < 5 and 7 <= local.hour < 18

def main():
    spam_folder = "spam"
    groups = defaultdict(int)
    group_emails = defaultdict(list)

    for eml in os.listdir(spam_folder):
        if not eml.endswith('.eml'): continue
        path = os.path.join(spam_folder, eml)
        with open(path, 'r', errors='ignore') as f:
            content = f.read()
            if not re.search(r'To:.*?cyfoinc\.one\.com', content, re.I): continue
            server = extract_received_servers(path)
            if not server: continue
            date = parse_date(path)
            groups[server] += 1
            group_emails[server].append(date)

    sorted_groups = sorted(groups.items(), key=lambda x: -x[1])
    if len(sorted_groups) < 3:
        print("Not enough groups.")
        return

    middle_group = sorted_groups[1][0]  # 2nd in sorted list
    valid_offsets = []
    for dt in group_emails[middle_group]:
        if dt and is_working_hours(dt):
            offset = dt.utcoffset().total_seconds() / 3600
            valid_offsets.append(offset)

    if not valid_offsets:
        print("No valid emails.")
        return

    # Find most common offset
    offset_counts = defaultdict(int)
    for offset in valid_offsets:
        offset_counts[offset] += 1
    common_offset = max(offset_counts, key=offset_counts.get)

    # Map offset to country (simplified)
    country_map = {
        1: 'DEU',   # Germany (UTC+1)
        2: 'EGY',   # Egypt (UTC+2)
        3: 'RUS',   # Russia (UTC+3)
        5.5: 'IND', # India (UTC+5.5)
        -5: 'USA',  # USA (UTC-5)
        0: 'GBR',   # UK (UTC+0)
    }
    closest = min(country_map.keys(), key=lambda x: abs(x - common_offset))
    print(f"Answer to Q17: {country_map[closest]}")

if __name__ == "__main__":
    main()