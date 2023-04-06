import math, pytz, csv, os, json
from tzlocal import get_localzone
from garmin_fit_sdk import Decoder, Stream

EMPTY_REC = 65535

def main ():
    for f in [f for f in os.listdir () if f[-4:].lower () == '.fit']:
        process_file (f, f[:-4] + '.csv')

def rr_records_size (records):
    i = 0
    for r in records:
        fields = r['developer_fields']
        if len (fields.items ()) != 1 \
                or not isinstance (fields[0], list):
            return False
        for v in fields[0]:
            if not isinstance (v, int):
                return False
            if not v == EMPTY_REC:
                i = i + 1
    return i

def process_file (source_file, destination_file):

    messages, errors = Decoder (Stream.from_file (source_file)).read ()

    if errors:
        print ("%s: Error decoding %s" % (source_file, str (errors)))
        return

    with open (source_file[:-4] + '.json', 'w') as f:
        f.writelines (json.dumps (messages, indent = 4, default = str))

    size = rr_records_size (messages['record_mesgs'])
    print ("%s: has %d records" % (source_file, size))
    if size < 1:
        return

    records = dict ()
    for msg in messages['record_mesgs']:
        for k, v in msg.items ():
            records[k] = []

    records['beat_intervals'] = []
    for msg in messages['record_mesgs']:
        fields = msg['developer_fields']
        rr = [r for r in fields[0] if not r == EMPTY_REC]
        for k, v in msg.items ():
            if k != 'developer_fields':
                for i in range (0, len (rr)):
                    records[k].append (v)
            else:
                records['beat_intervals'] += rr
    for k in [k for k in records.keys () if k not in {"beat_intervals", "timestamp", "heart_rate"}]:
        records.pop (k)

    if len (set ([len (v) for v in records.values ()])) != 1:
        print ("%s: with header %s" % (source_file, str ([k for k in records.keys ()])))
        print ("Different amount of records! " + str ([len (v) for v in records.values ()]))
        return

    # Validation
    duration_a = (max (records['timestamp']) - min (records['timestamp'])).total_seconds ()
    duration_b = sum (records['beat_intervals']) / 1000
    print ("%s: Logged %.1f seconds of %.1f beats" % (source_file, duration_a, duration_b))

    # Write to CSV file
    local_tz = get_localzone ()
    with open (destination_file, 'w') as f:
        csvfile = csv.writer (f)
        csvfile.writerow ([str (k) for k in records.keys ()])
        for i in range (0, size):
            row = []
            for k in records.keys ():
                v = None
                if k == 'timestamp':
                    v = records[k][i].replace (tzinfo=pytz.utc).astimezone (local_tz)
                # Convert to int so Spreadsheets can recognize for sure
                elif k == 'beat_intervals' or k == 'heart_rate':
                    v = int (records[k][i])
                else:
                    v = records[k][i]
                row.append (str (v))
            csvfile.writerow (row)

if __name__ == '__main__':
    main ()
