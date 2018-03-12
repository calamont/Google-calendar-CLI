import re
import time
import json
import datetime
import numpy as np
import pandas as pd
from schedule import Calendar


import os


class Experiment:

    def __init__(self, experiment_data):

        self.info = experiment_data
        self.experiment_label = self.info['label']
        self.start_date = experiment_data['start_date']

        # look at existing experiment files, ignoring anything hidden
        experiment_files = [f for f in os.listdir('experiment_dates') if not f.startswith('.')]
        self.num_of_experiments = len(experiment_files)

    def create_test_schedule(self):

        beginning = datetime.datetime(2018, 1, 1)  # mark the 'beginning' of the calender as the first monday of 2018 (which is the 1st anyway)
        time_elapsed = self.start_date - beginning  # the time (in days) elapsed since the beginning of the calendar (1/1/2018)
        self.time_elapsed = time_elapsed.days

        t_days = np.zeros(365)  # intialise array to incidate dates of tests. Will work for +13 yrs.

        saturdays = np.arange(5, 365, 7)
        sundays = saturdays + 1
        weekends = np.concatenate((saturdays, sundays))  # lists the day values which are weekends

        try:
            days = int(self.info['days'])
            num_of_weekends = (days // 7)  # count number of weekends
            t_days[self.time_elapsed: self.time_elapsed + days] = 1

            # remove weekends from dates to consider for experiments
            # for i in range(num_of_weekends):
            #     weekend_date = 7 * num_of_weekends - 2
            t_days[weekends] = 0

        except ValueError:
            # asign first measurement if no value given for days

            t_days[0] = 1

        try:
            weeks = int(self.info['weeks'])

            last_test = max(t_days.nonzero()[0])

            last_test = self.time_elapsed + 7 if ((last_test - 4) % 7) == 0 else last_test  # if last test was on a friday, the beginning of the weekly tests will be the following monday

            # days = 8 if days == 7 else days  # shifting start date if weekly measurements are meant to start after a week of daily measurements

            # week_dates = (np.arange(weeks + 1) * 7) + (days - 1)  # determine the days on which tests are performed, offset by original daily tests

            t_days[last_test: (last_test + weeks * 7) + 1: 7] = 1

            # test_days[week_dates] = 1

        except ValueError:

            # asigns zero value if nothing entered for days
            weeks = 0

        try:
            months = int(self.info['months'])

            last_test = max(t_days.nonzero()[0])

            # will treat months actually as 4 weeks
            t_days[last_test: (last_test + months * 28) + 1: 28] = 1

        except ValueError:

            # asigns zero value if nothing entered for days
            if self.info['months'] == 'end':

                t_days[(days - 1)::28] = 1
                print(t_days)

            else:
                print(self.info['weeks'])
                print('Maybe error with entered monthly value')

        self.test_days = t_days

    # def update_experiments(self):
    #     # update all previous experiment schedules to make sure there are no conflicts. Priority is given to whichever experiment is newest

    #     # need a function which will add and minus a day, two days etc. to a confilct until the less prioritised schedule doesn't conflict with the new schedule. Then this 'new' older schedule has to be compared to the next oldest shedule. If this next oldest schedule does have a conflict then we need to repeat the above method of removing this conflict, while comparing the result to the very newest and the next newest schedule. Continue until no more conflicts are found. All the while making sure the new dates don't fall on a weekend!


class Experiment_test:

    def __init__(self):
        # creation_time = datetime.datetime.now()
        # self.eventID = (self._creation_time - date

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
                self.get_schedule()  # work out the measurement days based on the input measurement frequencies

    def get_schedule(self):
        beginning = datetime.datetime(2018, 1, 1)  # mark the 'beginning' of the calender as the first monday of 2018 (which is the 1st anyway)
        time_elapsed = self.start_date - beginning  # the time (in days) elapsed since the beginning of the calendar (1/1/2018)
        self.time_elapsed = time_elapsed.days

        tests = np.zeros(365)  # intialise array to incidate dates of tests. Will work for +13 yrs.

        saturdays = np.arange(5, 365, 7)
        sundays = saturdays + 1
        weekends = np.concatenate((saturdays, sundays))  # lists the day values which are weekends

        tests[self.time_elapsed] = 1  # create the first experiment

        # assign daily experiments based on day values provided
        # num_of_weekends = (self.days // 7)  # count number of weekends

        tests[self.time_elapsed: self.time_elapsed + self.days] = 1  # create tests
        tests[weekends] = 0  # cancel any tests which were scheduled over a weekend

        # assign experiments based on week values provided
        if self.weeks:
            last_test = max(tests.nonzero()[0])  # find last test schedule in previous step
            last_test = self.time_elapsed + 7 if ((last_test - 4) % 7) == 0 else last_test  # if last test was on a friday, the beginning of the weekly tests will be the following monday

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
