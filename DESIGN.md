# Veritas & Varieties Design

---
## Table of Contents
1. HTML Layouts overview
2. app.py Overview
3. Backend Overview
4. Supplemental Code Overview
---
## HTML Layouts Overview

### layout.html
This HTML page is the layout that the other pages extend through Jinja so common features such as the navigation bar and footer do not have to be repeatedly coded across all the pages. The layout utilizes Bootstrap framework for responsiveness and mobile-friendliness. We also imported external Google Fonts to enhance visuals. We ensured through the existence of a navigation bar toggle button that the navigation bar is collapsible on smaller screens.

### homepage.html
The homepage begins with a hero section at the top implementing a scenic Boston skyline image overlaid with a title and subtitle. The main section is divided into the left side with the current date that is passed through from app.py and the right side with the list of events occurring that day, a list also passed through app.py that is then iterated through. If no events are found for the day, a message is displayed indicating there are no events scheduled. Beneath the list of events, a button is linked to the full event calendar. There is also a button for the backend to run, and in the future this would be restricted to only developers.

### week.html
This page dynamically generates a schedule by iterating through the `week_events` data, which is structured by day and contains event details for each day. The events are organized into sections with the day of the week as the header. If no events are scheduled for a particular day, a message is shown.

### calendar.html
The calendar page renders an interactive calendar to browse events by month. The page is structured to display a calendar grid where each day is represented by a div element. The header section includes a form with buttons to navigate between the previous and next months, sending a POST request with hidden fields to adjust the month and year displayed on the calendar. The calendar header is dynamically updated to show the current month and year based on current_month and current_year variables passed from the backend. Each day is conditionally styled with CSS classes based on its property of calendar-day-inactive, calendar-day-today, and calendar-day-before. Inside each day’s grid cell, each event details are shown. The event container also includes a `data-price` attribute to store event pricing information so that when each event is hovered over, the price is shown.

### random.html
This webpage features a button that uses a POST method to detect if the user responds to select a random event. If the event variable is populated, its details (name, time, location, description, and price) are shown in a structured format.

## app.py Overview

The app.py file is essential as the backend logic of the webpage of our application. This keeps the Flask and Python logic separate from the HTML. Early on in app.py, we set up a connection to the SQLite database `events.db` to simply execute SQL queries directly within the Flask app.

The `fetch_events_by_date` function queries the database to fetch events that match a specific date. It groups events by name and location to prevent duplicate events appearing on the webpage and selects the maximum price and minimum time in order to consolidate the list of events. We import `datetime` and calendar at the top to allow the code to efficiently handle date and time manipulation. We need this function across multiple pages on the website.


The `/homepage` function first processes events going on that day. It then utilizes threading to simultaneously run a function titled `update_events_backend` that calls on the backend to analyze the emails in the appropriate text file. The `update_events_backend` function then cleans the database to ensure we’re not querying irrelevant or outdated data, thus improving performance and decreasing storage. We wanted the two functions to run parallel so that the user is not waiting for the homepage to render every time they try to navigate there. Meanwhile, the `/homepage` continues to render the html template to feature the events occurring that day.

The `/week` function iterates through seven days and gathers events for each day using the `fetch_events_by_date` function. The use of a dictionary (week_events) to group events by day (day_name) makes the data structure easily accessible in the template. It minimizes the need for complex data manipulation in the template. It gathers all the necessary data for the next 7 days, formats it, and passes it to the template.

In the `/calendar` function, we have the POST method to handle user input for month navigation. The form data (month, year, direction) is parsed, and the month is incremented or decremented accordingly. The code calculates the first day of the month, adjusts the calendar grid to account for days from the previous month that spill over into the first week and then generates events for each day. The loop generates 35 days in total, which is five weeks to account for a full month view event if the month does not start perfectly on a Sunday. Each day is represented as a dictionary including the actual date, a flag to indicate whether the day belongs to the current month, and events, a list of events that occur on that specific date. This dictionary is then added to the calendar_days list that holds the data for each day.

The `/random` function handles both `GET` and `POST` methods, to ensure that a random event is only generated if the user submits the form. If the request is a `GET` (initial load), it simply renders the template without any event data. The SQL query `ORDER BY RANDOM() LIMIT 1` selects a random row from the events table. Then, the render_template function is used to dynamically render random.html with the selected event.

## Backend Overview

The function `process_emails_from_file`, called in app.py, accepts as an input the file `emails.txt`, which consists of the events manually aggregated from mailing lists that day, as well as the Gemini API key. First, in batches of three, the function calls on the class `GeminiExtractor` and specifically the `extract_events` function to utilize Gemini’s API to create a text output from processing that file.

The query for the Gemini is designed to return a list of dictionaries for each event in each of the emails. We run into the standard issue that the output of the Gemini function consists of a single string, not a dictionary, even if it looks like a dictionary. Therefore, our next step was to first delete the unnecessary json formatting from the output and then to parse it with `json.loads` to properly format it as a dictionary.

Having processed the emails and appropriately formatted the output, the backend.py returns the list of dictionaries for application in app.py.

## Supplemental Code Overview

Note when reviewing this section the commented-out sections of backend.py, the entirety of authenticate.py, credentials.json, token.json.

The Gmail API is far more complicated than the Gemini API, due to its focus on safety and sensitivity to data breaches. To work with the API, six major steps must be taken. 1) Access to the Gmail API must be requested through Google Cloud, the project must be authenticated and proper authorization as a testing user must be requested for the user in question; 2) an OAuth2 security credential, authorizing redirect URIs and access permissions, as well as necessary access scopes for the project (in our case .modify, since we aim to modify and delete old emails and read current ones) must be requested; 3) this credential, credentials.json, must be downloaded into the codespace, and the program must access this credential and use it to contact the Google server and request a token.json, an expiring security token that authorizes access to user sensitive data (Note 1); 4) in every implementation, the `token.json` and `credentials.json` must be tested and reauthorized if they have expired; 5) having established a connection to the Google server through authentication, the necessary functionality of the API must be exploited and email body extracted; 6) functionality must be established to rate-limit the API calls, delete old emails to prevent overuse of the API, and other data clearing measures must be implemented.

We demonstrate our work on each of these points in the following way:
1), 2) We completed the requests to the Google Cloud API and appropriately generated the credentials.json file with proper access credentials and correct redirect URIs, as well as correct scopes for our project, as can be seen by reading through `credentials.json`.

3) This was the main step that cost us our 15 hours of troubleshooting, as we had to learn the hard way that a) the secure connection with Gmail to receive the `token.json` is extremely picky and can be disrupted by everything, whether it’s an existing firewall, browser settings on chrome, security of the connection, the configuration of the WiFi network of access, the operation of cookies and Apache, the weather, the availability and typical usage patterns of particular ports, and updates to Google’s servers (only one of these was a joke). Additionally, we learned that it is impossible, due to the configuration of the GitHub codespace, to establish this secure connection through GitHub, and it requires the establishment of a local connection port and the use of VSCode as a local processor. Therefore, we ask that you do not attempt to run `authenticate.py` in GitHub, because it will not work - it should be run exclusively from a third-party codespace and run locally off one’s computer. Having overcome this hurdle, we successfully acquired a token.json, which one can verify by looking at the `token.json` and `authenticate.py` files.

4) Implementation for this can be seen in `backend.py`, where code is created to try to implement its productive functions, and, if a security credential is unavailable, to either throw up an error message (if the credential is `credentials.json`) or to attempt to retrieve it (unsuccessfully, but the triggering of these processes must signal to the developer that they need to run authenticate.py off VSCode.)

5) This is implemented successfully in class `EmailFetcher` to pull the body of emails and format them properly for later use.

6) In addition to only processing unread emails, our code also rate-limits calls on the Gmail and Gemini APIs to prevent an overcharge or catastrophic failure.

Through hard work on this function, we have mostly been able to create proper functionality. However, due to the time requirement of subsequently reconfiguring the code to accept the email input and thus refactoring and recreating a lot of our existing code, as well as remaking the formatting of the input into the Gemini function and creating different queues to maximize the productivity of the calls to the Gemini API (which have higher latency than calls to Gmail API, if excluding the hours one must wait to figure out how to access a security token), we chose to proceed with the project workaround and demonstrate the functions we have written that are fully operational while demonstrating the limited functionality of the full integration of the code as a supplemental demonstration of work.

Neither of the partners on this project knew when the project started how to work with APIs whatsoever. For the purpose of this project, we learned an extraordinary deal about enabling the functioning of APIs and security keys successfully accessing two APIs, and completing the progress of fully integrating one of them into our operating system. We are proud of this work and grateful for the opportunity to present its totality for consideration, even if it is in a supplemental way separate from the functionality.
