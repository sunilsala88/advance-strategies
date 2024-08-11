#strategy description:
#1. wait till 10:15 and calculate high and low from 9:15 to 10:15
#2. sell atm call and put option at 10:15
#3. if spot price goes above high, buy atm call option (closing loss making call position )
#4. if spot price goes below low, buy atm put option (closing loss making put position )
#5. after closing call position if spot price comes below high, sell atm call option again
#6. after closing  put position if spot price comes above low, sell atm put option again
#7. if the spot price is between high and low, do nothing
#8. checking for condition every 5 minutes
#9. closing all positions at 15:25


#https://drive.google.com/file/d/1n7TCW01s7QvuS3p47-N3TbHVpczutQkq/view


from datetime import datetime, timedelta  # Importing necessary modules
from calendar import monthrange, weekday, WEDNESDAY, THURSDAY
import pandas as pd
import time as t
import sqlite3
import logging
pd.options.mode.chained_assignment = None  # default='warn'

logging.basicConfig(filename='option_backtesting.log', filemode='w', level=logging.INFO, format=' %(message)s')  # Configuring logging
logging.info('this is my first line')  # Logging the first line


holidays = ['2021-01-26', '2021-03-11', '2021-03-29', '2021-04-02', '2021-04-14', '2021-04-21', '2021-05-13', '2021-07-21', '2021-08-19', '2021-09-10', '2021-10-15', '2021-11-04', '2021-11-05', '2021-11-19', '2022-01-26', '2022-03-01', '2022-03-18', '2022-04-14', '2022-04-15', '2022-05-03', '2022-08-09', '2022-08-15', '2022-08-31', '2022-10-05', '2022-10-24', '2022-10-26', '2022-11-08', '2023-01-26', '2023-03-07', '2023-03-30', '2023-04-04', '2023-04-07', '2023-04-14', '2023-04-21', '2023-05-01', '2023-06-28', '2023-08-15', '2023-09-19', '2023-10-02', '2023-10-24', '2023-11-14', '2023-11-27', '2023-12-25']
holidays = [datetime.strptime(x, '%Y-%m-%d') for x in holidays]  # Converting holiday strings to datetime objects


def get_weekly_expiry(year, month):  # Function to get all Thursdays of the month
    d = monthrange(year, month)[1]
    thursdays = [datetime(year, month, day) for day in range(1, d + 1) if datetime(year, month, day).weekday() == 3]
    for hol in holidays:
        if hol in thursdays:
            thursdays[thursdays.index(hol)] = hol - timedelta(days=1)  # Update Thursday to Wednesday if it's a holiday
    return thursdays

l=get_weekly_expiry(2023,1)
print(l)


def get_nearest_expiry(current_day=datetime.now()):
    # Get the current year and month based on the input 'current_day'
    year = current_day.year
    month = current_day.month

    # Calculate the last day of the current month
    last_day_of_month = monthrange(year, month)[1]

    # Find all Thursdays of the month
    thursdays = [datetime(year, month, day) for day in range(1, last_day_of_month + 1) if weekday(year, month, day) == THURSDAY]

    # Adjust Thursdays for holidays
    for hol in holidays:
        if hol in thursdays:
            # If a holiday falls on a Thursday, move it to the previous day (Wednesday)
            thursdays[thursdays.index(hol)] = hol - timedelta(days=1)

    # Find the current expiry date
    current_expiry = None
    for curr_thursday in thursdays:
        if current_day <= curr_thursday:
            current_expiry = curr_thursday
            break

    # Handle the case when today is after the last Thursday of the month
    if current_day > thursdays[-1]:
        if month == 12:
            # Move to the next year and set month to January
            year += 1
            month = 1
        else:
            month += 1

        # Calculate the Thursdays for the next month
        d = monthrange(year, month)[1]
        thursdays = [datetime(year, month, day) for day in range(1, d + 1) if weekday(year, month, day) == THURSDAY]

        # Adjust for holidays in the next month
        for hol in holidays:
            if hol in thursdays:
                # If a holiday falls on a Thursday, move it to the previous day (Wednesday)
                thursdays[thursdays.index(hol)] = hol - timedelta(days=1)

        current_expiry = thursdays[0]
        return current_expiry

    return current_expiry


a=get_nearest_expiry()
print(a)


def get_from_database():
    con = sqlite3.connect('option_history.db')
    cursorObj = con.cursor()
    cursorObj.execute('SELECT name from sqlite_master where type= "table"')
    data= cursorObj.fetchall()
    option_price_df={}
    for i in data:
        k=i[0]
        option_price_df[k]=pd.read_sql_query(f'SELECT * FROM {k}',con)
    return option_price_df




year=2023
month=1
money=2000
trades=open('trades.csv','w')
trades.write('time'+","+'option_contract_name' +","+'position'+','+'option_price'+','+'underlying_price'+','+'balance'+'\n')


start1 = datetime(year, month, 1)
option_price_df1=get_from_database()
option_price_df={}
#resample 1min to 5min and store in option_price_df

for i,j in option_price_df1.items():
    if j.empty == False:
        j=j[['datetime','open','high','low','close','volume']]
        j['datetime']=pd.to_datetime(j['datetime'])
        j.set_index('datetime',inplace=True)
        ohlcv_dict = {
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }
        option_price_df[i]=j.resample('5min').agg(ohlcv_dict)
        #drop nan rows
        option_price_df[i].dropna(inplace=True)
        #remove date before 9:15 and after 15:30
        option_price_df[i]=option_price_df[i].between_time('09:15','15:30')
        option_price_df[i].reset_index(inplace=True)

print(option_price_df)