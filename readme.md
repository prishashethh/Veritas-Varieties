# Veritas & Varieties Read Me

**Veritas & Varieties** is a platform designed to simplify event discovery for students and residents in Boston. By aggregating event information from a variety of sources, including Boston organization newsletters, and displaying it on an interactive calendar, the platform helps users stay informed and engaged with their community.

## Link To Our YouTube Video:
https://youtu.be/c5uKlm8s2vE

### Link To Our Supplemental Video:
https://youtu.be/l_vw_pYJNhI

---
## Table of Contents
1. [Overview](#overview)
2. [Features](#features)
3. [Setup Instructions](#setup-instructions)
4. [Usage Guide](#usage-guide)
5. [Technologies Used](#technologies-used)
6. [Known Issues](#known-issues)
7. [Future Improvements](#future-improvements)

---

## Overview
Veritas and Varieties automate the process of event discovery. First, we subscribed the email address petrsheth@gmail.com to various mailing lists from Boston organizations, including The Boston Calendar, The Boston Art Review, NBC Sports Boston, The Boston Globe, and Boston Loves Music. The project has designed an implementation for Gmail API to extract these emails and process them. Due to the challenge of privacy keys and the implementation of this process, while we have made substantial progress on the Gmail API front, we have chosen to instead make operational a simpler mechanism. Instead, on a daily basis, we copy the body contents of the emails into emails.txt. Using Gemini AI, the platform extracts key details (date, name, time, location, price, and description) about each event mentioned in each email, and then stores them in the database events.db. The database then feeds into a website that provides a user-friendly interface to allow users to view and explore upcoming events. Our goal is to provide a website for users to discover and plan their participation in local events without manually going through newsletters or other resources.

---

## Features
1. **Automated Event Aggregation**: The events are sourced from newsletters using Google’s Gemini AI-powered API, allowing us to gather information from the emails easily in proper format for the database.
2. **Interactive Calendar**: The website features an interactive calendar to display event information. The calendar allows the user to click through different months, so they have a preview if any events have already been posted for the future.
3. **Database Management**: The database ensures that no outdated events are present along with deleting incomplete entries. Also, if an event is publicized twice, and therefore present in our database twice, we ensure that it only appears on the user’s end once.
4. **User-Friendly Interface**: All in all, our website’s goal is to make the lives of Boston’s residents easier. We feature a clean homepage design that also gives easy viewing of the events taking place that day. Throughout our web pages, we highlight easy navigation and a focus on usability. There are also several ways for users to discover events they may be interested in, including a “Random” button which automatically generates a potential event!
5. **Set-up for Full Automation** We have worked more than 15 hours on implementing the Gmail API so that, in the future, no manual work whatsoever will be required to process the emails. The emails.txt file is a placeholder, and features for the Gmail API are even more comprehensive as we have implemented them, including:
Deletion of old emails, meaning that manual management of the file is not at all required
Flexibility with different kinds of emails and potential additional material, such as HTML, etc
The ability to successfully manage non-events-related emails, such as emails about the news and other topics

---
## Setup Instructions

### Installation
First, ensure the following package dependencies are downloaded:
`
- pip install google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2 (Google API for Gmail)
- pip install ratelimit (to stick within the free limits for API calls on Gmail and Gemini)
- pip install google-generativeai (for Gemini API)
- pip install logging (for logging purposes. This is our primary error management mechanism)
`

To start the Flask server, run:
` flask run `
Then open the webpage on the local port that appears.
To see the processing of the emails.txt file, look at the bottom of the page.
As a supplemental demonstration of our work, we have several functions and a large commented-out block of `backend.py`, which, though incomplete, in the terminal window, demonstrates serious progress in extracting email bodies and sending them through Gemini AI for processing.
---
## Usage Guide

The backend automatically updates the database with new events from `emails.txt` copied from the email newsletters whenever the homepage is loaded. Use the navigation bar at the top of each page to toggle between the events. On the Homepage, scroll down to view the events present that day. Click the calendar button to transfer over to the calendar view. On the Calendar view, hover over a specific event to view the price for that event. Additionally, use the buttons in line with the title to switch between the various months. The Week view is a static webpage. On the Random webpage, click the center button to generate a random event from our database that we recommend you go to. To see the process of the code and to see how the code handles the upload of the files, look at the terminal - we have made detailed logging of the code’s continued progress.

---
## Technologies Used

On the backend, we use ***Google’s Gemini AI AP*** to parse through the text file to extract event information from each email that is encoded in ***python***. Once the AI gathers information about the events, the event information is stored in a ***SQLite Database***. The basic structure and style of the website interface are done through ***HTML*** and ***CSS***. We use ***Flask*** in order to add dynamic elements to our website. We used ***threading*** to render the homepage while the backend was processed.

In the supplemental file, we use ***GMail API*** to process emails, including the use of ***OAuth 2 Security keys and tokens***, implemented through the ***Google Cloud***. The Gemini API was also accessed with the use of security keys in Google Cloud.

---
## Known Issues

Scaling is a challenge because of the way that security credentials are authorized and rate limits are done. Trying to scale this application would require paying Google to access higher API call caps. Additionally, while we’ve spent many hours (having consulted four TFs, three AI models, and countless other resources) working through the implementation of the Gmail API, some work is left to be completed in terms of the integration of its output into the broader code.

---
## Future Improvements
Some ideas we had for future implementation are:
1. *User Preferences*: Allow users to filter events by category, i.e. music, sports, educational
2. *Integration with Calendar*: Use Google Calendar and other calendar APIs for better cross-platform compatibility to sync upcoming events between the platform and the user’s calendar.
3. *Scalability*: Expand the database and backend to support a larger volume of event data, allowing the platform to cover more cities and organizations beyond Boston.
4. *User Preferences*: Create profiles for each user to allow personalized event suggestions based on users’ preferences, browsing history, and location.
5. *GMail API Implementation*: Complete the GMail API to create an entirely automated process that would require no user involvement on the backend of the website.

---
## Contact

For questions or issues, please contact us at:
prishasheth@college.harvard.edu (Prisha) and pberlizov@college.harvard.edu (Peter).

Thank you for using Veritas & Varieties! Also, thank you for a wonderful semester in CS50! So grateful for everything we learned and for all of your time leading this course.
