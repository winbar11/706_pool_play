Change Log
All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog and this project adheres to Semantic Versioning.

## Update
[0.2.0] - 2026.07.17
- backend scoring fix:
  - fixed courses set par to be dynamically pulled by API
  - was hardcoded at 72 showing incorrect scores

## Update
[0.1.1] - 2026.07.16
- UI bug fixes

## Update
[0.1.0] - 2026.07.07
- updated to SQLAlchemy for database actions
- added The Open Championship theme
  - created new logos for The Open Championship
- updated player field to '26 Open Championship field
- fixed minor visual bugs

## Update + Added
[0.0.16] - 2026.06.21
- fixed UI bug to show correct live scoring

## Update + Added
[0.0.15] - 2026.05.04
- 2026 U.S. Open field update
- new US Open UI theme
- Users can create up to 3 teams per tournament
- added 'Forgot Password' functionality to login page

## Fixed
[0.0.14] - 2026.04.09
- fixed lowest round bonus bug

## Updated + Added
[0.0.13] - 2026.04.08
- fixed how ties are shown on leaderboard page

## Updated + Added
[0.0.12] - 2026.04.08
- updated UI features in Admin page
- cleaned up & added more concise info to landing/home page
- added leaderboard truncation functionality
  - added player to always see where there team is located if they're not in the top 10

## Updated
[0.0.11] - 2026.04.06
- changed back missed cut/wd penalty back to +8
- added pot of gold UI & db persistence

## Added
[0.0.10] - 2026.04.06
- added landing page with signup info
- added back missed cut/wd penalty back to +8

## Added
[0.0.9] - 2026.04.05
- added more detial to leaderboard page
- added Masters player field with new DFS prices

## Added
[0.0.8] - 2026.04.03
- fixed leaderboard live calculation for current round
  - added '_In Progress_' detail if a player is still playing their round
- updated editing teams functionality
  - don't have to reselect all golfers again
- added & improved pool play rules page
- updated README.md with new scoring rules

## Added
[0.0.7] - 2026.04.02
- added rules page

## Updated
[0.0.6] - 2026.04.02
- updated to entirely new scoring engine

## Added/Fixed
[0.0.5] - 2026.04.02
- added clear scores admin functionality

## Added
[0.0.4] - 2026.04.01
- added entire field for Valero Texas Open testing
- converted logo to .svg image type
- added clear teams button

## Added
[0.0.3] - 2026.04.01
- added new css elements
- added new logo
- fixed ESPN API endpoint

## Added
[0.0.2] - 2026.03.25
- added front-end code (react-js)

## Added
[0.0.1] - 2026.03.25
- Initial Commit for masters_706
  - Backend (FastAPI) & sqllite code