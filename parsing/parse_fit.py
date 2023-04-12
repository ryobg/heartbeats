#!/usr/bin/env python

'''
@see https://en.wikipedia.org/wiki/Heart_rate_variability
A robust algorithm for heart rate variability time series artefact correction using novel beat classification
@see https://www.tandfonline.com/doi/abs/10.1080/03091902.2019.1640306 
'''

import pytz, csv, os, json, numpy, shutil, systole
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
            records = correct_intervals (records)
            target_file = source_file[:-4] + '.csv'
            write_to_csv (target_file, records)
            shutil.copy (target_file, "current.csv")
        except Exception as e:
            print ("Error: " + "".join (TracebackException.from_exception (e).format ()))
            continue

#-----------------------------------------------------------------------------------------------------------------------

def write_to_csv (destination_file, records):
    with open (destination_file, 'w') as f:
        csvfile = csv.writer (f, lineterminator = '\n')
        csvfile.writerow ([str (k) for k in records.keys ()])
        for i, _ in enumerate (list (records.values ())[0]):
            row = []
            for k in records.keys ():
                if i < len (records[k]):
                    row.append (str (records[k][i]))
                else:
                    row.append ("")
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

def correct_intervals (records):
    '''
    correct_rr() will operate on the RR time series directly and will return another time series that can have a 
    different timing (as the cumulative sum of the R interval will change). When we do not want this estimate to be 
    contaminated by extreme RR intervals or even smaller deviations, those intervals are corrected by interpolation to 
    make the time series as standard as possible, sacrificing the temporal precision of the heartbeat occurrence.

    correct_peaks() will operate on the peaks vector directly. The number of peaks (and therefore the RR intervals) can 
    vary, but the timing will remain constant. When the temporal precision of the heartbeat detection is relevant (this 
    can concern heartbeat evoked potentials or instantaneous heart rate variability when it is time-locked to some 
    specific stimuli. In this case, instead of blind interpolation, the raw signal time series can be used to 
    re-estimate the peaks.
    '''

    ibi = numpy.array (records['interbeat_intervals'], dtype = numpy.float64)
    ibi = ibi[(ibi > 10) & (ibi < 2000)]

    # Simple clean for the most obvious artifacts
    records['simple'] = [int (v) for v in ibi[ibi < 1700].tolist ()]
    print ("Simple clean removed %d intervals." % (len (records['interbeat_intervals']) - len (records['simple'])))

    # Recreate a new IBI time series that does not contain irregular intervals.
    ibi, _ = systole.correction.correct_rr (ibi)
    ibi = [int (v) for v in ibi.tolist ()]
    records['regular'] = ibi

    # Better detection of R peaks
    peaks = systole.correction.correct_peaks (ibi, input_type = "rr_ms", n_iterations = 2)
    peaks = systole.utils.input_conversion (peaks['clean_peaks'], input_type = "peaks", output_type = "rr_ms")
    records['peaks'] = [int (v) for v in peaks.tolist ()]

    return records

#-----------------------------------------------------------------------------------------------------------------------

def extract_records (record_msgs):
    '''
    @return dict of lists per timestamp, interbeat_intervals and heart_rate
    '''

    # Actually, only the IBI is what is interesting
    records = {"timestamp":[], "interbeat_intervals":[]}

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
    records.pop ('timestamp')

    # Type conversions (aka formatting in Spreadsheet applications)
    local_tz = get_localzone ()
    for i in range (0, len (records['interbeat_intervals'])):
        for k in records.keys ():
            if k == 'timestamp':
                records[k][i] = records[k][i].replace (tzinfo=pytz.utc).astimezone (local_tz)
            elif k == 'interbeat_intervals':
                records[k][i] = int (records[k][i])

    return records

#-----------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    main ()
