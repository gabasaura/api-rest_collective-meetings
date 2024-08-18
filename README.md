# Collective Meetings API
#### This project is an API designed to facilitate the scheduling of meetings by collecting availability from multiple participants and suggesting the best time slots based on their preferences. It is built with Flask and follows RESTful principles.

## Features
- User Roles: Users can be assigned roles as either creator, moderator, or guest.
- Meeting Management: Create and manage meetings with different privacy levels.
- Time Slot Rankings: Automatically rank time slots based on participant availability.
- Guest Participation: Invite guests via email to participate in meetings and submit their available time slots.
- Hashes for Security: Meetings and guest access are secured with generated hashes.
- Color-Coded Participation: Each participant is assigned a unique color for visualizing their availability.

## Usage

### Endpoints
- /meetings: Create, view, and manage meetings.
- /users: Manage users and their roles.
- /timeslots: Submit and view available time slots.
- /guests: Invite guests to meetings and manage their participation.

#### Refer to the API documentation for detailed information on each endpoint and its parameters.

### Example Workflow
- Create a Meeting: As a creator, create a new meeting and invite guests.
- Invite Guests: Guests receive an email with a unique link containing a hash to access the meeting.
- Submit Availability: Guests submit their available time slots.
- Rank Time Slots: The API ranks time slots based on the number of overlaps in availability.
- Finalize Meeting: Choose the best time slot and finalize the meeting.
