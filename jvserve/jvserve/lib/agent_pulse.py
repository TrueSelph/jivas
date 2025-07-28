"""Agent Pulse class for scheduling and running agent jobs."""

import logging
import threading
import time

import schedule


class AgentPulse:
    """Agent Pulse class for scheduling and running agent jobs."""

    EVENT = None
    THREAD = None
    LOGGER = logging.getLogger(__name__)

    @staticmethod
    def start(interval: int = 1) -> threading.Event:
        """Starts the agent pulse in a separate thread that executes
        pending jobs at each elapsed time interval.

        This method ensures that only one thread is running at a time
        to prevent duplication. If a thread is already running, it logs
        a message and returns without starting a new thread.

        @param interval: Time in seconds between each execution cycle of
        scheduled jobs.
        @return: threading.Event which can be set to stop the running
        thread.

        Note: It is intended behavior that run_continuously() does not
        run missed jobs. For instance, a job scheduled to run every
        minute with a run interval of one hour will only run once per
        hour, not 60 times at once.
        """

        if AgentPulse.THREAD and AgentPulse.THREAD.is_alive():
            AgentPulse.LOGGER.info("agent pulse is already running.")
            return AgentPulse.EVENT

        AgentPulse.EVENT = threading.Event()

        class ScheduleThread(threading.Thread):
            def run(self) -> None:
                while AgentPulse.EVENT and not AgentPulse.EVENT.is_set():
                    schedule.run_pending()
                    time.sleep(interval)

        AgentPulse.THREAD = ScheduleThread()
        AgentPulse.THREAD.start()

        AgentPulse.LOGGER.info("agent pulse started.")

        return AgentPulse.EVENT

    @staticmethod
    def stop() -> None:
        """Stops the agent pulse."""
        if AgentPulse.EVENT and not AgentPulse.EVENT.is_set():
            AgentPulse.LOGGER.info("agent pulse stopped.")
            AgentPulse.EVENT.set()
            if AgentPulse.THREAD:
                AgentPulse.THREAD.join()
