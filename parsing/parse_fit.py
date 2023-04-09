#!/usr/bin/env python

'''
@see https://en.wikipedia.org/wiki/Heart_rate_variability
A Real-Time Automated Point Process Method for Detection and Correction of Erroneous and Ectopic Heartbeats
@see https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3523127/
'''

import pytz, csv, os, json
from tzlocal import get_localzone
from garmin_fit_sdk import Decoder, Stream
from traceback import TracebackException

#-----------------------------------------------------------------------------------------------------------------------

EMPTY_REC = 65535

def main ():
    for source_file in [f for f in os.listdir () if f[-4:].lower () == '.fit']:

        print ("Processing " + source_file)

        messages, errors = Decoder (Stream.from_file (source_file)).read ()
        if errors:
            print ("Decoding error: " + str (errors))
            continue

        # Store a full, readable copy of the parsed FIT data.
        with open (source_file[:-4] + '.json', 'w') as f:
            f.writelines (json.dumps (messages, indent = 4, default = str))

        size = ibi_records_size (messages['record_mesgs'])
        print ("Amount of records: " + str (size))
        if size < 1:
            continue

        try:
            records = extract_records (messages['record_mesgs'])
            write_to_csv (source_file[:-4] + '.csv', records)
        except Exception as e:
            print ("Error: " + "".join (TracebackException.from_exception (e).format ()))
            continue

#-----------------------------------------------------------------------------------------------------------------------

def write_to_csv (destination_file, records):
    with open (destination_file, 'w') as f:
        csvfile = csv.writer (f)
        csvfile.writerow ([str (k) for k in records.keys ()])
        for i, _ in enumerate (records.values ()):
            row = []
            for k in records.keys ():
                row.append (str (records[k][i]))
            csvfile.writerow (row)

#-----------------------------------------------------------------------------------------------------------------------

def ibi_records_size (records):
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

#-----------------------------------------------------------------------------------------------------------------------

def extract_records (record_msgs):
    '''
    @return dict of lists per timestamp, interbeat_intervals and heart_rate
    '''

    # Actually, only the IBI is what is interesting
    records = {"interbeat_intervals":[], "timestamp":[], "heart_rate":[]}

    for msg in record_msgs:
        fields = msg['developer_fields']
        ibi = [r for r in fields[0] if not r == EMPTY_REC]
        for k, v in msg.items ():
            if k == 'developer_fields':
                records['interbeat_intervals'] += ibi
            elif k in records:
                records[k] += [v] * len (ibi)

    if len (set ([len (v) for v in records.values ()])) != 1:
        raise Exception ("Header {} amount of records mismatched {}".format (
            [k for k in records.keys ()], 
            [len (v) for v in records.values ()]))

    # Validation
    duration_a = (max (records['timestamp']) - min (records['timestamp'])).total_seconds ()
    duration_b = sum (records['interbeat_intervals']) / 1000
    print ("Activity duration: %.1fs, Interval beats duration: %.1fs" % (duration_a, duration_b))

    # Type conversions (aka formatting in Spreadsheet applications)
    local_tz = get_localzone ()
    for i in range (0, len (records['interbeat_intervals'])):
        for k in records.keys ():
            if k == 'timestamp':
                records[k][i] = records[k][i].replace (tzinfo=pytz.utc).astimezone (local_tz)
            elif k == 'interbeat_intervals' or k == 'heart_rate':
                records[k][i] = int (records[k][i])

    return records

#-----------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    main ()
