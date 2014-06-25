#!/usr/bin/python

import argparse
import glob
import re
import pickle
import os
import sqlite3
import smtplib
import socket
from jinja2 import Template
from datetime import datetime, timedelta
from settings import *

#processor to convert rows pulled from database to a dictionary
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
DATA_FILE = '{}/data.db'.format(SCRIPT_DIR)
HTML_TPL = '{}/index.html.tpl'.format(SCRIPT_DIR)
WWW_DIR = '/usr/share/nginx/www'
HOSTNAME = "http://" + socket.getfqdn()
try:
    PROBE = glob.glob('/sys/bus/w1/devices/28-*/w1_slave')[0]
except IndexError:
    print 'Could not find the temperature sensor file. Is the sensor attached?'


parser = argparse.ArgumentParser()
parser.add_argument('-n', '--notify',
                    help='notify if temperature above setpoints',
                    action='store_true')
parser.add_argument('-t', '--temperature', help='get current temperature',
                    action='store_true')
parser.add_argument('-r', '--record', help='record current temperature',
                    action='store_true')
parser.add_argument('-u', '--update', help='update webpage',
                    action='store_true')
parser.add_argument('-c', '--clean', help='remove old temperature readings',
                    action='store_true')
parser.add_argument('--testnotification', help='sends a test email',
                    action='store_true')
args = parser.parse_args()


def send_email(FROM, TO, contents):
    server = smtplib.SMTP(EMAIL_SERVER, EMAIL_PORT)
    server.ehlo()
    server.starttls()
    server.login(FROM_EMAIL, EMAIL_PASSWD)
    server.sendmail(FROM, TO, contents)
    server.close()


def send_notification(severity, temperature):
    TO = EMAILS
    FROM = FROM_EMAIL
    subject = 'Temperature {0}: {1} is {2} F'
    subject = subject.format(severity, LOCATION, temperature)
    text = 'Temperature in {0} is {1} F.\nSent from {2}'
    text = text.format(LOCATION, temperature, HOSTNAME)
    email = "From: {0}\nTo: {1}\nSubject: {2}\n\n{3}"
    email = email.format(FROM, ', '.join(TO), subject, text)
    send_email(FROM, TO, email)


def test_notification():
    TO = EMAILS
    FROM = FROM_EMAIL
    subject = "Test notification from {}".format(HOSTNAME)
    text = "This is a test notification."
    email = "From: {0}\nTo: {1}\nSubject: {2}\n\n{3}"
    email = email.format(FROM, ', '.join(TO), subject, text)
    send_email(FROM, TO, email)


def notify():
    # To be run every 5 minutes
    data = get_temperatures(start_date=(datetime.now() - timedelta(hours=1)))

    # Put data in list and sort so most recent readings are at the beginning
    # Data in list are a tuple: (temperature, time)
    temps = []
    for datum in data:
        temps.append((datum['temperature'], datum['time']))
    temps.sort(key=lambda time: time[1], reverse=True)

    current_temp = temps[0][0]
    five_min_ago = temps[1][0]

    if current_temp >= ALERT_TEMP:
        send_notification('alert', current_temp)
    elif current_temp >= WARNING_TEMP and \
            five_min_ago < WARNING_TEMP:
        send_notification('warning', current_temp)
    elif current_temp < WARNING_TEMP and \
            five_min_ago >= WARNING_TEMP:
        send_notification('okay', current_temp)


def clean():
    #database connection
    conn = sqlite3.connect('/opt/temperature/Temperature')
    c = conn.cursor()
    
    #delete any entries from the database older than RENENTION_DAYS
    c.execute("DELETE FROM temperature WHERE time < ?", (datetime.now() - timedelta(days=RETENTION_DAYS),))
    
    #save changes
    conn.commit()
    conn.close()
    
def read_temperature():
    checksum = ''
    temp = ''
    with open(PROBE, 'rb') as f:
        checksum = f.readline()
        temp = f.readline()

    re_checksum = re.compile(r'(?P<reading_good>YES)$')
    re_temp = re.compile(r'(?P<temperature>\d+$)')

    if re_checksum.search(checksum).group('reading_good') != 'YES':
        return None
    elif re_temp.search(temp).group('temperature') is None:
        return None
    else:
        temp = re_temp.search(temp).group('temperature')
        c_temp = int(temp) / 1000.0
        f_temp = (c_temp * (9.0 / 5.0)) + 32
        return f_temp


def record_temperature():
    temperature = read_temperature()

    conn = sqlite3.connect('/opt/temperature/Temperature')
    c = conn.cursor()
    
    #insert most recent read of the temp sensor along with current datetime into DB
    c.execute("INSERT INTO temperature (temperature, time) VALUES(?, ?)", (temperature, datetime.now()))
    
    #save changes
    conn.commit()
    conn.close()

def get_temperatures(start_date=(datetime.now() - timedelta(hours=24)),
                     end_date=datetime.now()):
    
    #sqlite connection that will retain the datetime data type in python
    conn = sqlite3.connect('/opt/temperature/Temperature', detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    
    #will use our dictionary function to insert data from fetchall into dictionary data 
    #structure when assigned to a variable. Essentially tells python when it creates a 
    #row when using the fetchall command to make sure that it uses the dictionary processing
    #function
    conn.row_factory = dict_factory
    
    c = conn.cursor()
    c.execute('SELECT temperature, time as "time [timestamp]" FROM temperature')

    #fetchall dumps all information from our query into a python variable (a dictionary due to our processing)
    data = c.fetchall()
    conn.close()
    
    return [datum for datum in data if start_date < datum["time"] < end_date]


def update_webpage():
    with open(HTML_TPL, 'rb') as f:
        template = f.read()
    hour_data = get_temperatures(start_date=(datetime.now() -
                                 timedelta(hours=1)))

    day_data = get_temperatures(start_date=(datetime.now() -
                                timedelta(hours=24)))

    week_data = get_temperatures(start_date=(datetime.now() -
                                 timedelta(days=7)))

    info = {
        'temperature': str(read_temperature())[:4],
        'location': LOCATION,
        'time': datetime.now().strftime('%B %d %I:%M %p'),
        'hour_data': hour_data,
        'day_data': day_data,
        'week_data': week_data,
    }

    template = Template(template)
    page = template.render(info)
    with open('{}/index.html'.format(WWW_DIR), 'wb') as f:
        f.write(page)
    

if args.testnotification:
    test_notification()
if args.temperature:
    print str(read_temperature())
if args.record:
    record_temperature()
if args.notify:
    notify()
if args.update:
    update_webpage()
if args.clean:
    clean()
