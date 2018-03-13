import os
import re
import datetime
import numpy as np


class Experiment:

    def __init__(self):
        # look at existing experiment files, ignoring anything hidden
        self._experiment_files = [f for f in os.listdir('experiment_dates') if not f.startswith('.')]
        self.num_of_experiments = len(self._experiment_files)

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, label_input):
        # ensure experiment label doesn't match previous experiments
        if label_input in self._experiment_files:
            raise ValueError("\nERROR: Experiment with this name already exists!")
        else:
            self._label = label_input

    @property
    def months(self):
        return self._months

    @months.setter
    # ensure only appropriate values entered for measurement duration
    def months(self, months_input):
        if not re.search(r'(^\d+$|^end$)', months_input):
            raise TypeError("\nERROR: Please enter either an integer or 'end' for measurement duration")
        else:
            self._months = months_input

    @property
    def start_date(self):
        return self._start_date

    @start_date.setter
    def start_date(self, date):
        if not re.search(r'^\d\d/\d\d/\d\d$', date):
            raise ValueError('\nERROR: Please enter date in the format dd/mm/yy.')

        else:
            self._start_date = datetime.datetime.strptime(date, '%d/%m/%y')

            if (self._start_date.date() - datetime.date.today()).days < 0:
                raise ValueError('\nERROR: Date provided is in the past.')
            elif self._start_date.weekday() > 4:
                raise ValueError('\nERROR: Date provided is on the weekend.')
            else:
                # work out the measurement days based on the input measurement frequencies
                self.get_schedule()

    def get_schedule(self):
        """Takes CLI input and returns schedule for that experiment"""

        # mark the 'beginning' of the calender as the first monday of 2018
        beginning = datetime.datetime(2018, 1, 1)
        # the time (in days) elapsed since the beginning of the calendar (1/1/2018)
        time_elapsed = self.start_date - beginning
        self.time_elapsed = time_elapsed.days

        tests = np.zeros(365)

        saturdays = np.arange(5, 365, 7)
        sundays = saturdays + 1
        # lists the day values which are weekends
        weekends = np.concatenate((saturdays, sundays))

        tests[self.time_elapsed] = 1  # create the first experiment

        tests[self.time_elapsed: self.time_elapsed + self.days] = 1  # create tests
        tests[weekends] = 0  # cancel any tests which were scheduled over a weekend

        # assign experiments based on week values provided
        if self.weeks:
            # find last test schedule in previous step
            last_test = max(tests.nonzero()[0])
            # if last test was on a friday, the beginning of the weekly tests will
            # be the following monday
            last_test = self.time_elapsed + 7 if\
                ((last_test - 4) % 7) == 0 else last_test
            tests[last_test: (last_test + self.weeks * 7) + 1: 7] = 1

        try:
            months = int(self.months)  # convert months from inputted string
            last_test = max(tests.nonzero()[0])
            # will treat months as 4 weeks
            tests[last_test: (last_test + months * 28) + 1: 28] = 1

        except ValueError:
            # asigns zero value if nothing entered for days
            if self.months == 'end':
                tests[(days - 1)::28] = 1
            last_test = max(tests.nonzero()[0])
            self.last_test = last_test
            print('final')

        self.measurement_days = tests
