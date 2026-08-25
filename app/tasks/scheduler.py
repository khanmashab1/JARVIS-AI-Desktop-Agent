"""Background reminder checker and non-blocking scheduler."""

import asyncio
from datetime import datetime
import threading
from typing import Callable, List, Optional

from app.memory.manager import MemoryManager
from app.memory.models import ReminderRecord
from app.utils.logging import get_logger

logger = get_logger("tasks.scheduler")


class ReminderScheduler:
    """Periodically inspects pending reminders and fires notifications."""

    def __init__(
        self,
        memory_manager: MemoryManager,
        on_reminder_triggered: Optional[Callable[[ReminderRecord], None]] = None,
        check_interval_seconds: float = 5.0,
    ) -> None:
        self.memory = memory_manager
        self.on_reminder_triggered = on_reminder_triggered
        self.check_interval_seconds = check_interval_seconds
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._loop_instance: Optional[asyncio.AbstractEventLoop] = None

    def start(self) -> None:
        """Start scheduler in dedicated background thread with its own event loop."""
        if self._running:
            return
        self._running = True

        def _runner():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._loop_instance = loop
            try:
                loop.run_until_complete(self._loop())
            except (asyncio.CancelledError, Exception) as ex:
                logger.debug(f"Scheduler loop exited: {ex}")
            finally:
                loop.close()

        self._thread = threading.Thread(target=_runner, daemon=True, name="reminder-scheduler")
        self._thread.start()
        logger.info("Reminder scheduler started in background thread.")

    def stop(self) -> None:
        self._running = False
        if self._loop_instance and self._loop_instance.is_running():
            self._loop_instance.call_soon_threadsafe(self._loop_instance.stop)
        logger.info("Reminder scheduler stopped.")

    async def _loop(self) -> None:
        while self._running:
            try:
                self.check_reminders()
            except Exception as e:
                logger.error(f"Error in scheduler tick: {e}")
            await asyncio.sleep(self.check_interval_seconds)

    def check_reminders(self) -> List[ReminderRecord]:
        """Check due reminders against current local time."""
        now_str = datetime.now().isoformat()
        pending = self.memory.list_reminders(include_completed=False)
        due_list: List[ReminderRecord] = []

        for reminder in pending:
            # Simple ISO or string comparison
            if reminder.due_time <= now_str or reminder.due_time.lower() in ("now", "immediately"):
                due_list.append(reminder)
                self.memory.complete_reminder(reminder.id)
                logger.info(f"Reminder triggered: {reminder.text}")
                if self.on_reminder_triggered:
                    try:
                        self.on_reminder_triggered(reminder)
                    except Exception as ex:
                        logger.error(f"Error in reminder callback: {ex}")

        return due_list
