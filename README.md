# Google-Calendar-CLI

A command line interface (CLI) created to help plan the schedule of lifetime experiments for my PhD and uploads this to Google Calendar using the [Google Calendar API](https://developers.google.com/calendar/). Each measurement on a set of samples takes approximately 8 hrs, with 10-15 batches of samples to measure at regular intervals in time. In addition, the equipment used for such measurements is also required by other researchers. The CLI allows one to create an experiment, set the frequency and interval of measurements to be performed over time (or if it is simply a one-off experiment for that day).

The program determines if there will be any clashes between the new experiment and any previously created experiments (as only one batch of samples can be measured each day). If there are clashes, the program will reschedule lower priority experiments until these are removed. 

---

#### The interface
<img src="https://github.com/calamont/Google-calendar-CLI/blob/master/example%20images/exp_details.png" alt="interface" width="500" height="whatever">
<img src="https://github.com/calamont/Google-calendar-CLI/blob/master/example%20images/exp_details.png" alt="frequency" width="500" height="whatever">

#### The result
<img src="https://github.com/calamont/Google-calendar-CLI/blob/master/example%20images/calendar.png" alt="calendar" width="500" height="whatever">
