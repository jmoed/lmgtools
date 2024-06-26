#!/usr/bin/python3

# powerlog95.py
#
# Log measured values from ZES Zimmer LMG95 Power Analyzer
#
# 2012-07, Jan de Cuveland

import argparse, sys, time, lmg95

#VAL = "count sctc cycr utrms itrms udc idc ucf icf uff iff p pf freq".split()
VAL = b"count utrms itrms p pf".split()


def main():
    parser = argparse.ArgumentParser(
        description = "Log measured values from ZES Zimmer LMG95 Power Meter")
    #parser.add_argument("host", help = "Hostname of RS232-Ethernet converter")
    parser.add_argument("logfile", help = "Log file name")
    parser.add_argument("-p", "--port", dest = "port", default=2001,
                        help = "TCP port of RS232-Ethernet converter")
    parser.add_argument("-v", "--verbose", dest = "verbose", type = int, default=0, help = "Verbose")
    parser.add_argument("-l", "--lowpass", dest = "lowpass", action="store_true", default=False,
                        help = "Enable 60 Hz low pass filter")
    parser.add_argument("-i", "--interval", dest="interval", type=float, default=1.0,
                        help = "Measurement interval in seconds")
    parser.add_argument("-r", "--reset", dest="reset",action='store_true', help = "Reset LMG")
    args = parser.parse_args()

    #print( "connecting to", args.host, "at port", args.port)
    print( "connecting at port", args.port)
    lmg = lmg95.lmg95(args.port)
     
    print( "performing device reset")
    lmg.reset()
     
    if args.reset:
      lmg.cont_off()
      return


    print( "device found:", lmg.read_id())

    print( "setting up device")
    errors = lmg.read_errors()

        # set measuremnt interval
    lmg.send_short_cmd(b"CYCL %d" % args.interval);

        # 60Hz low pass
    if args.lowpass == True:
        lmg.send_short_cmd("FAAF 0");
        lmg.send_short_cmd("FILT 4");

    #lmg.set_ranges(10., 250.)
    lmg.select_values(VAL)

    log = open(args.logfile, "w");
    i = 0
    try:
        lmg.cont_on()
        log.write("# time " + b" ".join(VAL).decode('ascii') + "\n")
        print( "writing values to", args.logfile)
        print( "press CTRL-C to stop")
        while True:
            data = lmg.read_values()
            i += 1
            data.insert(0, time.time())
            if args.verbose:
                sys.stdout.write(" ".join([ str(x) for x in data ]) + "\n")
            else:
                sys.stdout.write("\r{0}".format(i))
            sys.stdout.flush()
            log.write(" ".join([ str(x) for x in data ]) + "\n")
            log.flush()
    except KeyboardInterrupt:
        print()
     
    lmg.cont_off()
    log.close()

    lmg.disconnect()
    print( "done,", i, "measurements written")


if __name__ == "__main__":
    main()
