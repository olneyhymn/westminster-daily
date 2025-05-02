[![Code Climate](https://codeclimate.com/github/olneyhymn/westminster-daily/badges/gpa.svg)](https://codeclimate.com/github/olneyhymn/westminster-daily)

# Westminster Daily

Read through the [Westminster Standards](https://en.wikipedia.org/wiki/Westminster_Standards) in a year at [reformedconfessions.com](http://www.reformedconfessions.com). Based on [https://www.gpts.edu/resources/documents/Calendar%20Readings%20in%20WestminsterNumbered.pdf](Calendar of Readings in the Westminster Standards) by Dr. Joseph Pipa Jr.

## Setup and Development

Clone with `git clone https://github.com/olneyhymn/westminster-daily.git`.

Setup a virtualenv or Conda environment and run `pip install -r requirements.txt`.

### Building the Site

The site is built using Pandoc and a Makefile. The main commands are:

* `make all`: Build the entire site including HTML pages, RSS feeds, and assets
* `make build`: Build the site structure and compile CSS
* `make feed.rss`: Generate the main RSS feed
* `make podcast.rss`: Generate the podcast RSS feed

### RSS Feed Generation

The site uses tox to generate RSS feeds:

* `tox -e feed`: Generate the main RSS feed
* `tox -e podcastfeed`: Generate the podcast RSS feed

## Deployment

The site is automatically deployed to Netlify when changes are pushed to the main branch.

## Project Structure

* `content/`: Markdown source files for daily readings
* `static/`: Static assets including SCSS files
* `build/`: Generated site files
* `build_page.sh`: Script to convert Markdown to HTML using Pandoc