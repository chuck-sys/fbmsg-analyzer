'''
Facebook analytics tool. Requires a 2018-08-09 or later downloaded messages log.
Head to https://www.facebook.com/dyi for customizations. Make sure that you
select "JSON" for the formating.

Command-line tool for printing facebook messaging conversation analytics and
various statistics, including number of messages, time of messages, number of
emoji used, times of emoji usage, etc..

Everything is printed in Tab-Separated Values, so it is easy to copy and paste
everything printed out into your favourite spreadsheet program.

Defaults to hourly analysis which aggregates data based on time of day. Can also
do monthly analysis, where it analyzes message data based on month, or yearly
analysis of similar function.
'''
import argparse as ap
import json
from glob import glob
from operator import itemgetter
from functools import reduce
from datetime import datetime
from os.path import basename, join
from emoji import UNICODE_EMOJI

DATA_COLLECTED = {'msgs_sent': 'Messages sent',
                  'avg_msg_len': 'Avg message length',
                  'photos_sent': 'Photos sent',
                  'vids_sent': 'Videos sent',
                  'links_sent': 'Links shared',
                  'gifs_sent': 'GIFs sent',
                  'emojis_sent': 'Emoji sent',
                  'reactions': 'Reactions'}

INTERVALS = ['hourly', 'monthly', 'yearly']

def get_args():
    '''
    Gets all command-line arguments
    '''
    parser = ap.ArgumentParser(description=__doc__,
                               formatter_class=ap.RawTextHelpFormatter)

    parser.add_argument('folder', type=str, help='Folder to FB messages')
    parser.add_argument('-t', '--interval', default='hourly', type=str, choices=INTERVALS, help='Time interval for analysis')

    manual_group = parser.add_mutually_exclusive_group()
    manual_group.add_argument('-l', '--limit', type=int, default=5, help='Limit to relevant groups')
    manual_group.add_argument('-n', '--intelligent', action='store_true', help='Tries to choose without user intervention, which conversation you want')

    person_group = parser.add_mutually_exclusive_group(required=True)
    person_group.add_argument('-p', '--person', type=str, help='Person to search')
    person_group.add_argument('-i', '--interactive', action='store_true', help='Interactive mode')

    return parser.parse_args()

def get_relevant_msg_folders(root):
    '''
    Given the name of the root folder, gets the list of relevant folders that
    house the message.json file.
    '''
    folders = glob(join(root, 'messages', '*'))
    return filter(lambda f: basename(f).islower(), folders)

def score_relevance(folder, s):
    '''
    Given the name of the group, returns a score where the higher the score the
    more relevant the folder is to the group. A score of 0 means no relevancy.
    '''
    parts = s.lower().split(' ')
    return reduce(lambda a, part: a + int(part in folder), parts, 0)

def get_relevant_people_folders(folders, s):
    '''
    Given a list of folders and the name of the person, returns all folders
    relevant, in descending order of relevancy
    '''
    rels = filter(lambda f: score_relevance(f, s) > 0, folders)
    return sorted(rels, key=lambda f: score_relevance(f, s), reverse=True)

def select_relevant_convo(relevants):
    '''
    Given the relevant conversations, gets the one folder that the user wants
    to look through using `input()`.

    Lists out their options beforehand, and asks to type a number. Returns the
    folder-name of the selected conversation, or `None` if none are selected.
    '''
    # Make them look a bit prettier, first of all
    for i, folder in enumerate(relevants):
        # Opens the files to read the title
        msgs = json.load(open(join(folder, 'message.json')))
        print('[%d]\t%s' % (i, msgs['title']))

    try:
        u = int(input('Enter index [0-%d]: ' % (len(relevants) - 1)))
        if u >= 0 and u < len(relevants):
            return relevants[u]
        else:
            return None
    except:
        return None

def _create_stats():
    '''
    Returns a sub-statistics profile
    '''
    return {k: 0 for k in DATA_COLLECTED.keys()}

def create_stats(args):
    '''
    Returns a blank statistics profile, preferably for an interlocutor.
    '''
    general = _create_stats()

    if args.interval == 'hourly':
        general['int'] = {hr: _create_stats() for hr in range(24)}
    elif args.interval == 'monthly' or args.interval == 'yearly':
        general['int'] = {}

    return dict(general)

def count_emoji(s):
    '''
    Returns the number of emoji used in a string.
    '''
    unorthodox_counting = s.count('\\u') // 4
    orthodox_counting = reduce(lambda a, c: a + int(c in UNICODE_EMOJI.keys()), s, 0)

    return unorthodox_counting + orthodox_counting

def is_gif(p):
    '''
    Returns true if the given photo (p['uri']) is a GIF
    '''
    return '.gif' in p['uri']

def get_property(stats, prop, t=str):
    '''
    Returns a list of properties from the stats dictionary format mentioned
    above.
    '''
    participants = list(filter(lambda name: name != 'intervals', stats.keys()))

    return map(t, map(itemgetter(prop), map(lambda p: stats[p], participants)))

def get_interval_tsv(stats, interval):
    '''
    Returns TSV string of statistics based on interval given
    '''
    participants = list(filter(lambda name: name != 'intervals', stats.keys()))

    # Returns a dictionary of statistics of a given person by interval
    get_person_stats = lambda p: stats[p]['int'].get(interval, _create_stats())
    # Returns a list of keys of statistics of a given person by interval
    get_person_keys = lambda p: get_person_stats(p).keys()
    # Returns a TSV string of statistics of a given person, in order of keys
    get_combined_stats = lambda p: '\t'.join(map(lambda k: str(get_person_stats(p)[k]), get_person_keys(p)))

    return '\t'.join(map(get_combined_stats, participants))

def print_general_stats(stats):
    '''
    Prints all general statistics in TSV.
    '''

    for k, v in DATA_COLLECTED.items():
        print('%s\t%s' % (v, '\t'.join(get_property(stats, k))))

def print_interval_stats(stats, interval):
    '''
    Prints the statistics based on hourly, monthly, or yearly intervals
    '''
    if interval == 'hourly':
        for hr in range(24):
            print('%d\t%s' % (hr, get_interval_tsv(stats, hr)))
    elif interval == 'monthly' or interval == 'yearly':
        for interval in stats['intervals']:
            print('%s\t%s' % (interval, get_interval_tsv(stats, interval)))

def pretty_print_stats(stats, args):
    '''
    Prints the statistics prettily
    '''
    participants = list(filter(lambda name: name != 'intervals', stats.keys()))
    # Some general informations
    print('Total Messages sent\t%d' % sum(get_property(stats, 'msgs_sent', t=int)))
    print('Participants\t%s' % '\t'.join(participants))

    print()
    print_general_stats(stats)
    print()

    # Interval statistics
    ksizes = len(DATA_COLLECTED.keys())
    print('Order\t%s' % ''.join(map(lambda p: (p + '\t') * ksizes, participants)))
    print('Interval\t%s' % '\t'.join(list(DATA_COLLECTED.keys()) * len(participants)))
    print_interval_stats(stats, args.interval)

def get_correct_interval(stamp, args):
    '''
    Returns the correct interval given the timestamp and the arguments (only
    interval is required).
    '''
    if args.interval == 'hourly':
        return stamp.hour
    elif args.interval == 'monthly':
        return '%d-%02d' % (stamp.year, stamp.month)
    elif args.interval == 'yearly':
        return str(stamp.year)

def handle_content(stats, interval, msg):
    '''
    Handles all messages with content
    '''
    name = msg['sender_name']
    emojis = count_emoji(msg['content'])

    stats[name]['msgs_sent'] += 1
    stats[name]['avg_msg_len'] += len(msg['content'])
    stats[name]['emojis_sent'] += emojis
    stats[name]['int'][interval]['msgs_sent'] += 1
    stats[name]['int'][interval]['avg_msg_len'] += len(msg['content'])
    stats[name]['int'][interval]['emojis_sent'] += emojis

def handle_photos_and_gifs(stats, interval, msg):
    '''
    Handles all instances of messages with photos or GIFs
    '''
    name = msg['sender_name']
    photos = 0
    gifs = 0
    for p in msg.get('photos', []) + msg.get('gifs', []):
        if is_gif(p):
            gifs += 1
        else:
            photos += 1

    stats[name]['photos_sent'] += photos
    stats[name]['gifs_sent'] += gifs
    stats[name]['int'][interval]['photos_sent'] += photos
    stats[name]['int'][interval]['gifs_sent'] += gifs

def handle_videos(stats, interval, msg):
    '''
    Handles all messages with video content
    '''
    name = msg['sender_name']

    stats[name]['vids_sent'] += len(msg['videos'])
    stats[name]['int'][interval]['vids_sent'] += len(msg['videos'])

def handle_links(stats, interval, msg):
    '''
    Handles all messages with links
    '''
    name = msg['sender_name']

    stats[name]['links_sent'] += 1
    stats[name]['int'][interval]['links_sent'] += 1

def handle_reactions(stats, interval, msg):
    '''
    Handles all messages with reactions
    '''
    name = msg['sender_name']

    for rs in msg['reactions']:
        actor = rs['actor']

        if interval not in stats[actor]['int']:
            # Add the keys if they don't already exist
            stats[actor]['int'][interval] = _create_stats()

        stats[actor]['reactions'] += 1
        stats[actor]['int'][interval]['reactions'] += 1

def analyze(folder, args):
    '''
    Given the folder of the conversation to analyze, prints out (in TSV format)
    some statistics of the conversation.
    '''
    # First, do a bit of processing on the JSON (now python dict), because if
    # you don't, there will be a lot of duplicated code.
    with open(join(folder, 'message.json'), 'r') as fp:
        convo = json.load(fp)
        # Adds 'timestamp' into the dict, for each and every one of them
        for i in range(len(convo['messages'])):
            ts = convo['messages'][i]['timestamp_ms']
            ts = datetime.fromtimestamp(int(ts) / 1e3)
            convo['messages'][i]['timestamp'] = ts

    # Now, let's have fun.
    stats = {p['name']: create_stats(args) for p in convo['participants']}
    stats['intervals'] = []

    for msg in convo['messages']:
        # Calculate the interval first
        interval = get_correct_interval(msg['timestamp'], args)
        name = msg['sender_name']

        if interval not in stats['intervals']:
            # Add interval for quick reference later
            stats['intervals'].append(interval)
        if interval not in stats[name]['int']:
            # Add the keys if they don't already exist
            stats[name]['int'][interval] = _create_stats()

        if msg.get('content'):
            handle_content(stats, interval, msg)
        if msg.get('photos') or msg.get('gifs'):
            handle_photos_and_gifs(stats, interval, msg)
        if msg.get('videos'):
            handle_videos(stats, interval, msg)
        if msg.get('reactions'):
            handle_reactions(stats, interval, msg)
        if msg.get('share'):
            handle_links(stats, interval, msg)

    # Average out the average messages, actually
    for name in stats.keys():
        # Only names, please....
        if name == 'intervals': continue

        stats[name]['avg_msg_len'] /= stats[name]['msgs_sent']
        for interval in stats[name]['int'].keys():
            if stats[name]['int'][interval]['msgs_sent'] > 0:
                stats[name]['int'][interval]['avg_msg_len'] /= stats[name]['int'][interval]['msgs_sent']

    pretty_print_stats(stats, args)

def main():
    '''
    Main function. Linter please shut up.
    '''
    args = get_args()

    convos = list(get_relevant_msg_folders(args.folder))

    if args.person:
        relevants = get_relevant_people_folders(convos, args.person)[:args.limit]
        relevant = None

        if relevants:
            relevant = relevants[0]
        else:
            print('Could not find %s. Please try again.' % args.person)

        if not args.intelligent:
            relevant = select_relevant_convo(relevants)

        if relevant:
            analyze(relevant, args)
    elif args.interactive:
        relevants = None
        relevant = None

        while not relevant:
            query = input('What conversation do you want to search for?\n')
            relevants = get_relevant_people_folders(convos, query)[:args.limit]

            if relevants:
                relevant = select_relevant_convo(relevants)
                analyze(relevant, args)
            else:
                print('Could not find `%s`. Please try again.' % query)

if __name__ == '__main__':
    main()
