import time
from datetime import datetime, timedelta

##now = time.time
##print(now())
duration = 222133/1000.0

def stopwatch(seconds):
    start = time.time()
    # time.time() returns the number of seconds since the unix epoch.
    # To find the time since the start of the function, we get the start
    # value, then subtract the start from all following values.
    time.clock()
    # When you first call time.clock(), it just starts measuring
    # process time. There is no point assigning it to a variable, or
    # subtracting the first value of time.clock() from anything.
    elapsed = 0
    while elapsed <= seconds:
        elapsed = time.time() - start
        #print "loop cycle time: %f, seconds count: %02d" % (time.clock() , elapsed) 
        d = datetime(1,1,1)+ timedelta(seconds=elapsed)
        print("%02d:%02d" % (d.minute, d.second))
        time.sleep(1)
        # Notice that the process time is almost nothing.
        # This is because we are spending most of the time sleeping,
        # which doesn't count as process time.
        # For funsies, try removing "time.sleep()", and see what happens.
        # It should still run for the correct number of seconds,
        # but it will run a lot more times, and the process time will
        # ultimately be a lot more. 
    
stopwatch(duration)
