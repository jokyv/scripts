#!/usr/bin/env python

# -----------------------------------------------
# LIBRARIES
# -----------------------------------------------

from datetime import datetime

# -----------------------------------------------
# VARIABLES
# -----------------------------------------------

DATE_NOW = datetime.now()

# -----------------------------------------------
# FUNCTIONS
# -----------------------------------------------


def day_for_notes(date_now: datetime):
    """
    Get the current date and time.

    Format the date as "Day of the week, Year-Month-Day"

    Parameters
    ----------
    date_now : datetime
        Current local datetime from datetime.datetime

    """
    formatted_date = date_now.strftime("%A, %Y-%m-%d")
    print(formatted_date)


# -----------------------------------------------
# MAIN
# -----------------------------------------------


def main() -> None:
    day_for_notes(DATE_NOW)


if __name__ == "__main__":
    main()
