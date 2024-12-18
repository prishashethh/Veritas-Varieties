import os
import json
import logging  # Add logging
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from datetime import datetime, timedelta, date
from calendar import monthrange
import threading
import backend

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///events.db")

# Set up logging
logging.basicConfig(level=logging.INFO,  # Set logging level to INFO
                    format="%(asctime)s [%(levelname)s] %(message)s",
                    handlers=[
                        logging.StreamHandler(),  # Log to console
                        logging.FileHandler("app.log", encoding="utf-8")  # Log to a file
                    ])
logger = logging.getLogger(__name__)  # Create logger for this module

# Returns events occuring on a specific date


def fetch_events_by_date(date):
    return db.execute("""
            SELECT name,
                   MAX(price) AS price,
                   MIN(location) AS location,
                   MIN(date) AS date,
                   MIN(time) AS time,
                   MIN(description) AS description
            FROM events
            WHERE date = ?
            GROUP BY name
            ORDER BY time
        """, date)


@app.after_request
def after_request(response):
    # Ensure responses aren't cached
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Webpage for random
@app.route("/random", methods=["GET", "POST"])
def random():
    if request.method == "POST":
        # Select a random event from the list
        selected_event = db.execute("SELECT * FROM events ORDER BY RANDOM() LIMIT 1;")
        return render_template("random.html", event=selected_event[0])

    # If the method is GET
    else:
        return render_template("random.html")

# Webpage for week


@app.route("/week", methods=["GET"])
def week():
    """Show events for the next 7 days"""
    today = datetime.now()

    # Create a dictionary to hold events for each day of the next 7 days
    week_events = {}

    # Generate the dates for the next 7 days
    for i in range(7):
        day_date = today + timedelta(days=i)
        day_name = day_date.strftime("%A")  # e.g., "Monday", "Tuesday"
        formatted_date = day_date.strftime("%B %d, %Y")  # e.g., "November 27, 2024"
        day_formatted = day_date.strftime("%Y-%m-%d")  # e.g., "2024-11-26"

        # Query events for this specific day, making sure there are no duplicate days
        events = fetch_events_by_date(day_formatted)

        # Add events for this day to the dictionary
        week_events[day_name] = {
            "date": formatted_date,
            "events": events
        }

    return render_template("week.html", week_events=week_events)

# Returns the month of the year


@app.template_filter('month_to_number')
def month_to_number(month_name):
    return datetime.strptime(month_name, "%B").month

# Webpage for calendar


@app.route("/calendar", methods=["GET", "POST"])
def calendar():
    # Get today's date
    today = datetime.today()

    # Handle month navigation
    if request.method == "POST":
        current_month = int(request.form.get("month", today.month))
        current_year = int(request.form.get("year", today.year))
        direction = request.form.get("direction")

        if direction == "next":
            if current_month == 12:
                current_month = 1
                current_year += 1
            else:
                current_month += 1
        elif direction == "prev":
            if current_month == 1:
                current_month = 12
                current_year -= 1
            else:
                current_month -= 1
    else:
        current_month = today.month
        current_year = today.year

    # Get calendar details
    first_day = date(current_year, current_month, 1)

    # Create calendar grid
    calendar_days = []
    current_date = first_day

    # Find the first day of the week for the calendar grid
    while current_date.weekday() != 6:  # 6 is Sunday
        current_date -= timedelta(days=1)

    # Generate 35 days (5 weeks) for the calendar grid
    for _ in range(35):
        is_current_month = current_date.month == first_day.month

        # Fetch events for this date
        events = fetch_events_by_date(current_date.strftime('%Y-%m-%d'))

        # Create a list inside of a list that includes a list of events
        calendar_days.append({
            'date': current_date,
            'is_current_month': is_current_month,
            'events': events
        })

        current_date += timedelta(days=1)

    # Render the event with all the necessary components
    return render_template(
        "calendar.html",
        calendar_days=calendar_days,
        current_month=first_day.strftime("%B"),
        current_year=current_year,
        today=today
    )

# Updates the database in a seperate function to be able to run parallel


def update_events_backend():
    try:
        # Path to the file containing emails
        email_file_path = 'emails.txt'  # Update this path if necessary
        gemini_api_key = 'AIzaSyAnft9RxmB0XGPb9JuBDBf7suYAn9XtF6s'

        # Process emails using the updated function
        try:
            events = backend.process_emails_from_file(email_file_path, gemini_api_key)
        except Exception as e:
            logger.error(f"Error reading or processing emails from file: {str(e)}")
            events = []  # Default to empty list if there is an error

        if not events:
            logger.warning("No events found in the email file.")

        # Insert the event into the database
        for event in events:
            event_date = event['Date'] or "Not Available"
            event_name = event['Name'] or "Not Available"
            event_time = event['Time'] or "Not Available"
            if event_time != "Not Available":
                if event_time[2] != ":":
                    placeholder_event_time = event_time[:2] + ":" + event_time[2:]
                    event_time = placeholder_event_time
            event_location = event['Location'] or "We're sorry, not available"
            event_description = event['Description'] or "Not Available"
            event_price = event['Price'] or "Not Available"

            # Insert event into database
            db.execute("""
                INSERT INTO events (date, name, time, location, description, price)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                       event_date,
                       event_name,
                       event_time,
                       event_location,
                       event_description,
                       event_price
                       )
        # Get today's date
        today = datetime.today()
        day_str = today.strftime("%Y-%m-%d")
        current_time_str = today.strftime("%H:%M")
        print("Hello! This is Peter. Yay!")

        if not day_str or not current_time_str:
            raise ValueError("Invalid date or time format")

        # Log parameters for debugging
        logger.info(f"Executing query with day_str={day_str}, current_time_str={current_time_str}")

        # Remove past events from the database
        try:
            today = datetime.today()
            db.execute("""
                DELETE FROM events
                WHERE date < :day
                OR (date = :day AND time < :current_time)
            """, day=today.strftime("%Y-%m-%d"), current_time=today.strftime("%H:%M"))

            # Remove events missing three or more pieces of information
            db.execute("""
                DELETE FROM events
                WHERE ((name = 'Not Available')
                + (location = 'We're sorry, not available')
                + (time = 'Not Available')
                + (description = 'Not Available')) >= 2
                OR (date = 'Not Available')
            """)
        except Exception as e:
            raise e
            logger.error(f"Error executing query: {str(e)}")
            print(f"Error executing query: {str(e)}")
    except Exception as e:
        logger.error(f"Error in homepage route: {str(e)}")
        return render_template("error.html", error_message=str(e))

# Webpage for homepage


@app.route("/", methods=["GET", "POST"])
def homepage():
    today = datetime.today()
    day_str = today.strftime("%Y-%m-%d")
    # Fetch today's events from the database
    today_events = fetch_events_by_date(day_str)

    # If no events occuring, have a backup
    if not today_events:
        today_events = [{
            'name': 'No Events Today!',
            'price': 'Free',
            'location': 'Anywhere!',
            'date': day,
            'time': 'All Day',
            'description': 'Take a break, relax, and enjoy some peace! 🧘‍♂️🍹'
        }]
    if request.method == "POST":
        # Run the backend task in a separate thread
        threading.Thread(target=update_events_backend).start()

    # Render the homepage
    return render_template(
        "homepage.html",
        today_events=today_events,
        current_date=today
    )
