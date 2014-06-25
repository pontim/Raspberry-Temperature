#!/usr/bin/python

from subprocess import call
from shlex import split
from argparse import ArgumentParser
import logging
import os
import sys
import shutil
import glob
import sqlite3


# Install script-specific settings
script_dir = os.path.dirname(os.path.realpath(__file__))
script_log = '/var/log/temperature_install.log'

# Install locations for temperature monitoring stuff
www_dir = '/usr/share/nginx/www'
base_dir = '/opt/temperature'

# Parse command line arguments
parser = ArgumentParser()

install_help = 'install or update required packages/modules/folders'
parser.add_argument('-i', '--install', help=install_help, action='store_true')

fix_stuck_help = 'fix sensor if it will not update. Removes history'
parser.add_argument('-f', '--fix-stuck', help=fix_stuck_help, action='store_true')

verbose_help = 'enable verbose output'
parser.add_argument('-v', '--verbose', help=verbose_help, action='store_true')

debug_help = 'enable debug output'
parser.add_argument('-d', '--debug', help=debug_help, action='store_true')

args = parser.parse_args()

# Set up logging
logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                    filename=script_log, level=logging.DEBUG)

console = logging.StreamHandler()
if args.debug:
    console.setLevel(logging.DEBUG)
elif args.verbose:
    console.setLevel(logging.INFO)
else:
    console.setLevel(logging.WARNING)

formatter = logging.Formatter('%(levelname)s: %(message)s')
console.setFormatter(formatter)

logging.getLogger('').addHandler(console)
log = logging.getLogger('')


def run(command):
    log.debug('running shell command: {0}'.format(command))
    call(split(command))


def mkdir(path):
    if not os.path.isdir(path):
        if os.path.exists(path):
            log.warning('{0} exists and is not a directory; deleting it'
                        .format(path))
            try:
                os.remove(path)
            except OSError:
                log.critical('{0} is not a directory and can\'t be \
                             removed; exiting'.format(path))
                sys.exit(1)
        else:
            log.info('creating {0}'.format(path))
            try:
                os.makedirs('{}'.format(path), 0755)
            except OSError:
                log.critical('unable to create {0}; exiting'.format(path))
                sys.exit(1)
    else:
        log.info('directory {0} already exists; taking no action'.format(path))


def install_files():
    mkdir(base_dir)
    try:
        log.info('copying index.html.tpl to {0}'.format(base_dir))
        shutil.copy('{0}/index.html.tpl'.format(script_dir), base_dir)

        log.info('copying temperature.py to {0}'.format(base_dir))
        shutil.copy('{0}/temperature.py'.format(script_dir), base_dir)
        os.chmod('{}/temperature.py'.format(base_dir), 0755)

        log.info('copying data.db to {0}'.format(base_dir))
        shutil.copy('{0}/data.db.example'.format(script_dir), "{0}/data.db".format(base_dir))
        os.chmod('{}/data.db'.format(base_dir), 0755)

        log.info('copying temperature.py to {0}'.format(base_dir))
        shutil.copy('{0}/settings.py.example'.format(script_dir), "{0}/settings.py".format(base_dir))
        os.chmod('{}/settings.py'.format(base_dir), 0755)

        log.info('removing existing contents from {}'.format(www_dir))
        files = glob.glob(www_dir + '/*')
        for f in files:
            try:
                os.remove(f)
            except:
                shutil.rmtree(f)

        log.info('copying css/ to {0}'.format(www_dir))
        shutil.copytree('{0}/css'.format(script_dir), www_dir + '/css')

        log.info('copying js/ to {0}'.format(www_dir))
        shutil.copytree('{0}/js'.format(script_dir), www_dir + '/js')

        # Connect/Create SQLite database
        conn = sqlite3.connect('{0}/Temperature'.format(base_dir))
        c = conn.cursor()

        # Create table to hold data if it doesn't exist
        c.execute("""CREATE TABLE IF NOT EXISTS temperature(temperature DECIMAL(10,5) ,time DATETIME)""")
        conn.close()
    except OSError:
        log.critical('unable to copy files into place; exiting')
        raise
        sys.exit(1)


def get_config_info():
    info = {}
    info['hostname']
    info['hostname'] = raw_input('hostname [rpi-temp-sensor]: ')
    info['domain'] = raw_input('domain [local]: ')
    dhcp = raw_input('Use DHCP? [y/N]: ').lower()
    if dhcp[0] == 'y':
        info['dhcp'] = True
    else:
        info['dhcp'] = False
        info['ip'] = raw_input('IP address: ')
        info['netmask'] = raw_input('netmask [255.255.255.0]: ')
        ip_split = info['ip'].split('.')
        default_gateway = '{}.{}.{}.1'.format(ip_split[0], ip_split[1],
                                              ip_split[2])
        info['gateway'] = raw_input('gateway [{}]:'.format(default_gateway))
        info['dns'] = raw_input('DNS servers [8.8.8.8 8.8.4.4]:').split()

    info['location'] = raw_input('sensor location [Server Room]: ')
    info['warning_temp'] = raw_input('warning temperature [75]: ')
    info['alert_temperature'] = raw_input('alert temperature [80]: ')

    email_notification = raw_input('Do you want to set up email \
                                   notifications? [Y/n]: ').lower()
    if email_notification[0] == 'y':
        info['email_notification'] = True
        info['email_account'] = raw_input('Gmail account name: ')
        info['email_password'] = raw_input('Gmail account password: ')
        info['email_recipients'] = raw_input('email notification recipients \
                                             (separate with spaces): ').split()
    else:
        info['email_notification'] = False

    sms_notification = raw_input('Do you want to set up SMS \
                                 notifications [y/N]: ').lower()
    if sms_notification[0] == 'y':
        info['sms_notification'] = True
        print "All numbers should be in the format: +12062871000"
        info['twilio_sid'] = raw_input('Twilio SID: ')
        info['twilio_token'] = raw_input('Twilio token: ')
        info['twilio_number'] = raw_input('Twilio number to send SMSs from: ')
        info['sms_recipients'] = raw_input('SMS notification recipients \
                                           (separate with spaces)').split()
    else:
        info['sms_notification'] = False
    return info


def install_packages():
    log.info('installing nginx')
    run('apt-get -y install nginx')
    log.info('installing python and python libraries')
    run('apt-get -y install python')
    run('apt-get -y install python-matplotlib python-jinja2 python-pip')
    run('pip install twilio')
    run('service nginx start')


def install_kernel_modules():
    run('modprobe w1-gpio')
    run('modprobe w1-therm')
    with open('/etc/modules', 'wb') as f:
        f.write('w1-gpio\nw1-therm')


def make_cronjobs():
    cron = '* * * * * /opt/temperature/temperature.py -run\n'
    cron += '@daily /opt/temperature/temperature.py -c\n'
    with open('/tmp/tempcron', 'wb') as f:
        f.write(cron)
    run('crontab /tmp/tempcron')
    os.remove('/tmp/tempcron')


def fix_stuck():
    log.info('removing {0}/Temperature'.format(base_dir))
    os.remove('{0}/data.db'.format(base_dir))

    log.info('creating blank DB in {0}'.format(base_dir))
    # Connect/Create SQLite database
    conn = sqlite3.connect('{0}/Temperature')
    c = conn.cursor()

    # Create table to hold data if it doesn't exist
    c.execute("""CREATE TABLE IF NOT EXISTS temperature(temperature DECIMAL(10,5) ,time DATETIME)""")
    conn.close()

    log.info('recording temperature and updating site')
    run('{0}/temperature.py -r'.format(base_dir))
    run('{0}/temperature.py -r'.format(base_dir))
    run('{0}/temperature.py -run'.format(base_dir))


if __name__ == '__main__':
    if os.geteuid() != 0:
        print 'You must run this script as root'
        sys.exit(1)
    if args.install:
        install_packages()
        install_files()
        install_kernel_modules()
        make_cronjobs()
        sys.exit(0)
    if args.fix_stuck:
        fix_stuck()
        sys.exit(0)
