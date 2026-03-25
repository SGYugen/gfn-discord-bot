# GFN Discord Bot

A Discord bot for GeForce NOW error code lookup. When a user posts a message containing an error code (e.g. `0xC0F52132`), the bot fetches information from a JSON file and replies with the description and solutions.

## Project Structure

- `bot.py` - Main Discord bot script
- `data/errors.json` - Known error codes with descriptions and solutions
- `data/detected_errors.json` - Tracks newly detected error codes from Reddit
- `scripts/reddit_scraper.py` - Script that scrapes Reddit for new GFN error codes and sends alerts via Discord webhook

## Setup

### Environment Variables / Secrets

- `TOKEN` - Discord bot token (required to run the bot)

### Dependencies

- `discord.py` - Discord API library
- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing

## Running

The bot runs via the "Start application" workflow using `python bot.py`. Since this is a Discord bot (not a web app), it uses the `console` output type with no port.

## Features

- Listens for messages containing `0x` hex error codes
- Looks up error info from `data/errors.json` (or fetches from GitHub raw URL)
- Replies with error description and suggested solutions
- Reddit scraper script can be run manually to detect new error codes
