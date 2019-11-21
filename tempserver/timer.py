class Timer:
    _next_available_id = 0

    def __init__(self, scheduler, notify_change, name="Unknown", initial_time=0):
        self.id = "timer-" + str(Timer._next_available_id)
        self.name = name
        self.initial_time = initial_time
        self.remaining_time = initial_time
        self.running = False
        self.notify_change = notify_change

        scheduler.add_job(self.process_timer, 'interval', seconds=1, id="timer_iteration %s" % self.id)

        Timer._next_available_id += 1

    def set_name(self, name):
        if name == self.name:
            return

        self.name = name
        self.publish_state()

    def set_running(self, running):
        if running == self.running:
            return

        self.running = running
        self.publish_state()

    def set_initial_time(self, initial_time):
        if initial_time == self.initial_time:
            return

        self.initial_time = initial_time
        self.publish_state()

    def set_remaining_time(self, remaining_time):
        if remaining_time == self.remaining_time:
            return

        self.remaining_time = remaining_time
        self.publish_state()

    def process_timer(self):
        if self.running:
            self.remaining_time -= 1
            self.publish_state()

    def publish_state(self):
        if self.notify_change:
            self.notify_change((self.id, self))
