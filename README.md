[![Code Climate](https://codeclimate.com/github/olneyhymn/westminster-daily/badges/gpa.svg)](https://codeclimate.com/github/olneyhymn/westminster-daily)

# Westminster Daily

Read through the [Westminster Standards](https://en.wikipedia.org/wiki/Westminster_Standards) in a year at [reformedconfessions.com](http://www.reformedconfessions.com). Based on [https://www.gpts.edu/resources/documents/Calendar%20Readings%20in%20WestminsterNumbered.pdf](Calendar of Readings in the Westminster Standards) by Dr. Joseph Pipa Jr.

## Setup and Development

Clone with `git clone https://github.com/olneyhymn/westminster-daily.git`.

### Building the Site

The site is built using Pandoc and a Makefile. The main commands are:

* `make all`: Build the entire site including HTML, RSS feeds and assets
* `make build`: Build the site structure and compile CSS
* `make feed.rss`: Generate the main RSS feed
* `make podcast.rss`: Generate the podcast RSS feed

### RSS Feed Generation

The site uses python to generate RSS feeds:

* `uv run generate_feed.py`: Generate the main RSS feed
* `uv run generate_podcast_feed.py`: Generate the podcast RSS feed

## Deployment

The site is automatically deployed to Netlify when changes are pushed to the main branch.

## Automated Builds

The site is automatically rebuilt every day at 05:00 UTC using a GitHub Actions workflow. This ensures that the daily readings are always up to date. The workflow can also be triggered manually through the GitHub Actions interface.

## Project Structure

* `content/`: Markdown source files for daily readings
* `static/`: Static assets including SCSS files
* `build/`: Generated site files
* `build_page.sh`: Script to convert Markdown to HTML using Pandoc