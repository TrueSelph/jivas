import schedule;
import logging;
import traceback;
import from logging { Logger }

walker pulse {

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    class __specs__ {
        static has private: bool = True;
        static has schedule: dict = {
            "trigger": "interval",
            "seconds": 1, # Run every second
            "save": False
        };
    }

    can enter with entry {
        schedule.run_pending();
    }

}