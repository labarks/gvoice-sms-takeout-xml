from bs4 import BeautifulSoup
import os
import phonenumbers
import time, datetime
from calendar import timegm
import warnings

import tkinter as tk
from tkinter import filedialog

root = tk.Tk()
root.withdraw()

file_path = filedialog.askopenfilename()

"""
TO DO:
filter emoji
fix double-double quotes
"""

sms_backup_filename = "./gvoice-all.xml"

def main():

    num_sms = 0
    root_dir = '.'

    for subdir, dirs, files in os.walk(root_dir):
        for file in files:
            sms_filename = os.path.join(subdir, file)
            #print(sms_filename)

            try:
                sms_file = open(sms_filename, 'r')
            except FileNotFoundError:
                continue

            if(os.path.splitext(sms_filename)[1] != '.html'):
                print(sms_filename,"- skipped")
                continue
            print(sms_filename)

            soup = BeautifulSoup(sms_file, 'html.parser')

            messages_raw = soup.find_all(class_='message')

            num_sms += len(messages_raw)

            sms_values = {'phone' : get_phone(messages_raw)}

            for i in range(len(messages_raw)):
            ##        print('Unix time:',get_time_unix(messages_raw[i]))
            ##        print('Sender:',get_phone(messages_raw[i]))
            ##        print('Type:',get_message_type(messages_raw[i]))
            ##        print('Message text:',get_message_text(messages_raw[i]))
            ##        print('-----')
                sms_values['type'] = get_message_type(messages_raw[i])
                sms_values['message'] = get_message_text(messages_raw[i])
                sms_values['time'] = get_time_unix(messages_raw[i])
                sms_text = ('<sms protocol="0" address="%(phone)s" '
                            'date="%(time)s" type="%(type)s" '
                            'subject="null" body="%(message)s" '
                            'toa="null" sc_toa="null" service_center="null" '
                            'read="1" status="1" locked="0" /> \n' % sms_values)
                sms_backup_file = open(sms_backup_filename, 'a')
                sms_backup_file.write(sms_text)
                sms_backup_file.close()

    sms_backup_file = open(sms_backup_filename, 'a')
    sms_backup_file.write('</smses>')
    sms_backup_file.close()

    write_header(sms_backup_filename, num_sms)

def get_message_type(message): # author_raw = messages_raw[i].cite
    author_raw = message.cite
    if ( not author_raw.span ):
        return 2
    else:
        return 1

    return 0

def get_message_text(message):
    return BeautifulSoup(message.find('q').text,'html.parser').prettify(formatter='html').strip().replace('"',"'")

def get_phone(messages):
    for author_raw in messages:
        if (not author_raw.span):
           continue

        sender_data = author_raw.cite

        try:
            phone_number = phonenumbers.parse(sender_data.a['href'][4:], None)
        except phonenumbers.phonenumberutil.NumberParseException:
            return sender_data.a['href'][4:]

        if(phone_number.country_code == 1):
            return phonenumbers.format_number(phone_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)[1:].replace(' ', '-')
        else:
            return phonenumbers.format_number(phone_number, phonenumbers.PhoneNumberFormat.E164)
    return 0

def get_time_unix(message):
    time_raw = message.find(class_='dt')
    ymdhms = time_raw['title']
    time_obj = datetime.datetime.strptime(ymdhms.replace('Z','UTC'), '%Y-%m-%dT%H:%M:%S.%f%Z')
    #print('GV Date: ', ymdhms)
    #mstime = time.mktime(time_obj.timetuple()) * 1000 + time_obj.microsecond / 1000
    mstime = timegm(time_obj.timetuple()) * 1000 + time_obj.microsecond / 1000
    return int(mstime)

def write_header(filename, numsms):
    backup_file = open(filename, 'r')
    backup_text = backup_file.read()
    backup_file.close()

    backup_file = open(filename, 'w')
    backup_file.write("<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>\n")
    backup_file.write("<!--Converted from GV Takeout data -->\n")
    backup_file.write('<smses count="' + str(numsms) + '">\n')
    backup_file.write(backup_text)
    backup_file.close()
    
main()
