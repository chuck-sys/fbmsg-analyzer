# Facebook Messenger Analyzer

A small(ish) python script that analyzes your facebook messages, so you don't
have to! No other python packages are required, but python3 is a must.

## Requirements

Please download a copy of your Facebook data. The only thing needed is
'messages' folder - you don't need to download the rest if you don't want to.
Make sure you download all your data in **JSON** format, and not HTML. The photo
quality is unimportant - the script is only concerned with your message logs.

## Quick Start

```
python analyze.py -p "John Smith" ~/Downloads/fb-data
```

This will have the script search for a "John Smith". It will pick the 5 most
likely candidates and let you pick which conversation to analyze. Then, it will
analyze the conversation and you will see tab-separated values in your standard
output.

## Usage

To let the script determine the most likely candidate on it's own, add the `-n`
flag.

```
python analyze.py -p "John Smith" -n ~/Downloads/fb-data
```

To do analysis on a month-by-month or year-by-year basis, use the `-t` flag.

```
python analyze.py -p "John Smith" -n -t monthly ~/Downloads/fb-data
```

For more information, check out the help page.

```
python analyze.py -h
```

## Acknowledgements

`emoji.py` was partially copied from
https://github.com/carpedm20/emoji/blob/master/emoji/unicode_codes.py, just for
it's ability to check for emoji.
