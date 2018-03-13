import ast
import sys
import json
import datetime
import progressbar
import numpy as np
import pandas as pd
from random import choice
from shutil import copyfile
from textwrap import dedent
from collections import OrderedDict

import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

SCOPES = 'https://www.googleapis.com/auth/calendar'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Calendar API Python Quickstart'


class Calendar:

    def __init__(self):
        """Gets valid user credentials from storage.

        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.

        """
        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir,
                                       'calendar-python-quickstart.json')

        store = Storage(credential_path)
        self.credentials = store.get()
        if not self.credentials or self.credentials.invalid:
            flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
            flow.user_agent = APPLICATION_NAME
            if flags:
                self.credentials = tools.run_flow(flow, store, flags)
            else:  # Needed only for compatibility with Python 2.6
                self.credentials = tools.run(flow, store)
            print('Storing credentials to ' + credential_path)

        self.http = self.credentials.authorize(httplib2.Http())
        self.service = discovery.build('calendar', 'v3', http=self.http)

        # load existing calendar file with previous test dates
        self.initialise_schedule()

    def initialise_schedule(self):
        """Load existing calendar file with previous test dates"""
        if os.path.exists('data.json'):
            with open('data.json', 'r') as file:
                # Use OrderedDict to keep the priority of the experiments added.
                data = json.load(file, object_pairs_hook=OrderedDict)
                self.calendar = pd.DataFrame.from_dict(data)
                # Get int type of index - which are imported as strings and unordered
                new_index = [int(x) for x in self.calendar.index]
                self.calendar.set_index(keys=[new_index], inplace=True)
                self.calendar.sort_index(inplace=True)
        # If calendar does not exist, create it
        else:
            self.calendar = pd.DataFrame(index=range(365))

        self.experiment_labels = self.calendar.columns

    def add(self, experiment):
        """Insert new dates into calendar attribute"""
        self.new_experiment = experiment

        # Insert new experiment in the first column of dataframe to give it highest priority
        try:
            self.calendar.insert(loc=0, column=self.new_experiment.label,
                                 value=self.new_experiment.measurement_days)
        except ValueError as e:
            # shouldn't need this exception as the name is already checked at an earlier stage..
            print('\nAn experiment with that name already exists. Please try recreating an experiment with a different name.')
            sys.exit()

        # reschedule older, lower priority experiments so there are not two tests on the same day
        self.correct_collisions()

        self.save_dataframe()

    def save_dataframe(self):
        # write new schedule to file, which allows schedule to be amended in the future
        with open('data.json', 'w') as file:
            # converting json string to file type
            json_file = json.loads(self.calendar.to_json(),
                                   object_pairs_hook=OrderedDict)
            json.dump(json_file, file, indent=2)

    def correct_collisions(self):
        # convert dataframe to array
        self.create_array()

        # truncate calendar to only include dates from the beginning
        # of the experiment being added
        present_calendar = self.calendar_array[self.new_experiment.time_elapsed:, :]

        # update calendar instance with updated test schedule
        self.calendar_array[self.new_experiment.time_elapsed:, :] =\
            self.update_test_dates(present_calendar)
        self.calendar.iloc[:, :] = self.calendar_array[:, 1:]

    def create_array(self):
        # create weekends to prevent collision correction placing an "experiment"
        # on sat/sundays
        saturdays = np.arange(5, 365, 7)
        sundays = saturdays + 1
        # lists the day values which are weekends
        weekends = np.concatenate((saturdays, sundays))

        self.calendar_array = np.zeros((365, 1))
        self.calendar_array[weekends, :] = 1

        # concacentate weekend array and experiment array together, giving weekends
        # highest priority so new experiments won't get placed on these days
        self.calendar_array = np.concatenate(
            (self.calendar_array, self.calendar.values), axis=1)

    def update_test_dates(self, present_calendar):
        test_count, collisions, free_days = self.analyse_calendar(present_calendar)
        # remember to clear previous Google calendar events
        self.collisions = True if len(collisions) > 0 else False
        count = 0
        # recalculate and move test schedules while there are days with collisions
        # in the test calendar
        while len(collisions) > 0:
            # break out of program if caught in endless loop / taking too long
            count += 1
            if count > 1000000000:
                print('Cannot find optimal solution to scheduling calendar. Too many experiments currently listed')
                sys.exit()

            # iterate through days collisions detected on
            for day in collisions:
                tests = present_calendar[day, :]

                collision_tests = np.where(tests == tests.max())
                oldest_test = np.max(collision_tests)  # get oldest test in collision

                # determine nearest free day in schedule
                try:
                    day_differences = free_days - day
                    min_date = np.argmin(np.abs(day_differences))  # index of closest day

                except ValueError:
                    print('There are no free days left in the existing timeframe :(\nPlease delete or downsample the frequency of lower priority experiments.')
                    sys.exit()

                day_delta = day_differences[min_date]  # number of days from collision date
                # determine which direction the nearest free day is (past or future)
                direction = np.sign(day_delta)

                new_date = day + direction

                present_calendar[new_date, oldest_test] += 1
                present_calendar[day, oldest_test] -= 1

                test_count, collisions, free_days = self.analyse_calendar(present_calendar)

        return present_calendar

    def analyse_calendar(self, schedule):
        daily_test_count = np.sum(schedule, axis=1)
        collisions = np.where(daily_test_count > 1)[0]
        free_days = np.where(daily_test_count == 0)[0]

        return daily_test_count, collisions, free_days

    def Google_update(self):
        '''
        Function updates the saved experiment dates. It first creates text
        files which lists all the dates which have been designated for the
        experiments, which is then used to update the google calendar.
        Text files are created to serve as an offline reference, and in case
        of any errors which occur after this.
        '''

        # clear all previously set calendar events if there are event collisions
        if self.collisions:
            self.clear_calendar(cli=False)

        # create new dataframe to save data to a txt file from
        txt_calendar = self.calendar.copy()
        date_index = pd.DatetimeIndex(start=datetime.date(2018, 1, 1),
                                      periods=365, freq='D')
        txt_calendar.set_index(date_index, inplace=True)  # convert integers in index to dates

        print('\nUploading updated test schedule to the Solartron Google calendar...')

        # initialising progressbar to show progress of event creation
        self.num_of_experiments = txt_calendar.sum(axis=0).sum(axis=0)
        self.bar = progressbar.ProgressBar(maxval=self.num_of_experiments,
                                           widgets=[
                                               progressbar.Bar('◼', '', '', '◻'),
                                               progressbar.Percentage()])
        self.upload_count = 0
        self.bar.start()
        for column in txt_calendar.columns:
            # get array of dates from indices where experiments are
            # listed (i.e. 1 instead of 0 in calendar array)
            experiment_dates = txt_calendar[txt_calendar[column] == 1].\
                loc[:, column].index.date
            # convert array of datetime objects to a list of strings
            experiment_dates = [datetime.datetime.strftime(date, '%d/%m/%y')
                                for date in experiment_dates]
            # create random unique identifiers for the calendar eventIDs
            experiment_IDs = [''.join(choice('abcdefghijklmnopqrstuv0123456789')
                                      for i in range(10)) for j in experiment_dates]
            event_information = list(zip(experiment_dates, experiment_IDs))

            # save previous version of experiment schedule
            if os.path.exists(f'experiment_dates/{column}'):
                copyfile(f'experiment_dates/{column}', f'experiment_dates/archive/{column}')

            # write new experiment file with list of dates generated for the experiment
            with open(f'experiment_dates/{column}', 'w') as file:
                file.write(f'{event_information}')

            # create new google calendar events for this column and the experiment dates listed
            self.upload_experiments(column, event_information)
            # sys.stdout.flush()

        self.bar.finish()

    def upload_experiments(self, experiment_name, event_information):

        for date, eventID in event_information:
            self.upload_count += 1
            self.bar.update(self.upload_count)  # increment progress bar with upload
            UTCdate = datetime.datetime.strptime(date, '%d/%m/%y').strftime('%Y-%m-%dT')
            start_time = UTCdate + '09:00:00.00'
            end_time = UTCdate + '17:00:00.00'

            test_event = {
                'id': eventID,
                'creator': {
                    'displayName': 'Callum Lamont',
                    'email': 'callum.lamont.15@ucl.ac.uk'
                },
                'summary': experiment_name,
                'start': {
                    'timeZone': 'Europe/London',
                    'dateTime': start_time
                },
                'location': 'IDG Room 116A',
                'end': {
                    'timeZone': 'Europe/London',
                    'dateTime': end_time
                },
            }

            self.service.events().insert(
                calendarId='nllc88qbvtkks5a7jquivl9ibc@group.calendar.google.com',
                body=test_event).execute()

    def clear_calendar(self, exp_name='all', cli=True):
        print('\nClearing old schedule from the Solartron Google calendar...')
        if exp_name == 'all':
            delete_labels = self.experiment_labels
        else:
            delete_labels = [exp_name]

        for experiment in delete_labels:
            # first - remove all events from Google calendar
            with open(f'experiment_dates/{experiment}', 'r') as file:
                event_info = ast.literal_eval(file.read())  # read in exp file as list
                for date, eventID in event_info:
                    self.service.events().delete(
                        calendarId='nllc88qbvtkks5a7jquivl9ibc@group.calendar.google.com', eventId=eventID).execute()
            if cli:
                # If requested from the command line interface delete ALL traces of the experiment
                os.remove(f'experiment_dates/{experiment}')
                if os.path.exists(f'experiment_dates/archive/{experiment}'):
                    os.remove(f'experiment_dates/archive/{experiment}')

        # third - remove experiment column from DataFrame - Only perform if requested from the CLI
        if cli:
            self.calendar.drop(delete_labels, axis=1, inplace=True)
            self.save_dataframe()
