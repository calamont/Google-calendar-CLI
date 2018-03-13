import os
import time
import click
import datetime
from textwrap import dedent
from experiment import Experiment
from schedule import Calendar


@click.command()
def main():
    '''
    Walks through a command line interface which allows the use to
    manage a Google calendar listing experiments for a piece
    of equipment
    '''
    clear_screen()

    calendar = Calendar()
    test = program_selection()

    # Add new experiment
    if test == '1':
        experiment = create_experiment()
        calendar.add(experiment)
        calendar.Google_update()

    # Delete experiment
    elif test == '2':
        exp_delete = delete_experiment()
        calendar.clear_calendar(exp_delete, cli=True)

    clear_screen()


def program_selection():
    '''
    Prompts user to select how they would like to update the Solartron
    google calendar.

    Inputs can only be 1 or 2.

    '''
    return click.prompt('The options for updating the Solartron Google calendar are.. \n(1) Add experiment \n(2) Delete experiment\n\nSelect what option you would like to perform', type=click.Choice(['1', '2']))


def create_experiment():
    '''
    Prompts user for information regarding experiment they would like
    to create.

    • label = name of experiment
    • schedule = the frequency of measurements (i.e. daily/monthly)
      and total duration of experiment
    • start_date = the date from which to begin the experiment.
      Defaults to the current date

    '''
    exp = Experiment_test()

    # Request unique name for the experiment
    while True:
        try:
            exp.label = request_name()
        except ValueError as e:
            # Will raise a ValueError if the name requested already exists for
            # another experiment
            click.echo(e)
            time.sleep(2)
        else:
            break

    # Request timeline/schedule for the experiment
    single_test = click.confirm('\nIs this a one off experiment? (i.e. only using the Solartron for a single day)')
    if single_test:
        # Create single test for the date requested
        exp.days, exp.weeks, exp.months = request_schedule(single_test)
    else:
        clear_screen()
        # Request more information about the schedule of the experiment
        click.echo('Please indicate the length of the experiment, and the duration for which each measurement frequency will be performed.\n\nFor example, if you wished to perform daily measurements for 1 week, then weekly measurements for 1 month, then monthly measurements thereafter, the response required is..\n\nDaily measurements (days): 7\nWeekly measurements (weeks): 4\nMonthly measurements (months): end\n\n• To signify that you wish to keep performing monthly measurements indefinitely at a particular frequency, enter "end" instead of a number\n\n • To skip past a particular frequency, hit enter.')

        while True:
            try:
                exp.days, exp.weeks, exp.months = request_schedule(single_test)
            except ValueError as e:
                # Will raise ValueError if integers or 'end' not provided
                click.echo(e)
                time.sleep(2)
            else:
                break

    # Request start date for the experiment
    while True:
        try:
            exp.start_date = request_start()
        except ValueError as e:
            # Will raise ValueError if the date provided is in the wrong format.
            click.echo(e)
            time.sleep(2)
        else:
            confirm_date = click.confirm(f'\nYou entered {exp.start_date.date()}. Is this correct?')
            if confirm_date:
                break  # Move forward if correct date entered
    return exp


def delete_experiment():
    '''Prompts user for the name of the experiment they would like to delete.'''

    # Get experiment file names which can be deleted
    experiment_files = [f for f in os.listdir('experiment_dates') if
                        (os.path.isfile(os.path.join('experiment_dates', f)) and not f.startswith('.'))]

    experiment_string = ['• ' + name + '\n' for name in experiment_files]
    experiment_string = ''.join(experiment_string)
    # Prompt use to delete a file from this list
    return click.prompt('Which experiment would you like to delete? \n' +
                        experiment_string + '\n', type=click.Choice(experiment_files))


def request_name():
    '''Prompt user for a unique name for the experiment being created'''
    return click.prompt('\nPlease provide a label for the experiment. For CANDO experiments, these should be a single letter (i.e. A or G)')


def request_schedule(single_test):
    '''Prompt user for the experiment details relating to testing frequency'''
    if single_test:
        days = 1
        weeks = 0
        months = '0'
    else:
        days = click.prompt('\nDaily measurements(days)', type=int, default=0)
        weeks = click.prompt('Weekly measurements(weeks)', type=int, default=0)
        months = click.prompt('Monthly measurements(months)', type=str, default='0')
    return [days, weeks, months]


def request_start():
    '''Prompts user for the start date of the experiment being created'''
    clear_screen()
    today = datetime.datetime.today().strftime('%d/%m/%y')
    return click.prompt('Please enter the start date for your experiment (dd/mm/yy) (If the start date is today, then simply press Return)', type=str, default=today)


def clear_screen():
    '''Clears the terminal screen. Will work on Unix or Windows'''
    os.system('cls' if os.name == 'nt' else 'clear')


if __name__ == "__main__":
    main()
