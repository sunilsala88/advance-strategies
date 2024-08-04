#calc brik size
#calculate renko brick every second
#if 2 green brick and macd min candle crossover go long
#if 2 red brick and macd min candle crossover go short
#close all position by eod



import pandas as pd
import datetime 
import time
from ib_insync import *
import pandas as pd
import pandas_ta as ta
import asyncio

import logging
logging.basicConfig(level=logging.INFO, filename=f'super_{datetime.date.today()}',filemode='a',format="%(asctime)s - %(message)s")

ib = IB()
ib.connect('127.0.0.1', 7497, clientId=18)


try:
    order_filled_dataframe=pd.read_csv('order_filled_list.csv')
    order_filled_dataframe.set_index('time',inplace=True)

except:
    column_names = ['time','ticker','price','action']
    order_filled_dataframe = pd.DataFrame(columns=column_names)
    order_filled_dataframe.set_index('time',inplace=True)




tickers = ['RELIANCE','CUMMINSIN','ASHOKA']
exchange='NSE'
currency='INR'
account_no='DU6327991'
ord_validity='GTC'
quantity_=1
#start time
start_hour,start_min=10,41
#end time
end_hour,end_min=14,59

macd_xover = {}
renko_param = {}
latest_price={}

contract_objects={}
for ticker in tickers:
    c=ib.qualifyContracts(Stock(ticker,exchange, currency))[0]
    print(c)
    contract_objects[ticker]=c
print(contract_objects)




def order_open_handler(order):
    global order_filled_dataframe
    if order.orderStatus.status=='Filled':
        print('order filled')
        logging.info('order filled')
        name=order.contract.localSymbol
        a=[name,order.orderStatus.avgFillPrice,order.order.action]
        # if name not in order_filled_dataframe.ticker.to_list():
        order_filled_dataframe.loc[order.fills[0].execution.time] = a
        order_filled_dataframe.to_csv('order_filled_list.csv')
        message=order.contract.localSymbol+" "+order.order.action+"  "+str(order.orderStatus.avgFillPrice)
        logging.info(message)




def get_historical_data(ticker_contract,bar_size,duration):
    logging.info('fetching historical data')
    bars = ib.reqHistoricalData(
    ticker_contract, endDateTime='', durationStr=duration,
    barSizeSetting=bar_size, whatToShow='MIDPOINT', useRTH=True,formatDate=1)
    # convert to pandas dataframe:
    df = util.df(bars)
    print(df)
    logging.info('calculated indicators')
    df['ema']=ta.ema(df.close, length=20)
    df['super']=ta.supertrend(df.high,df.low,df.close,length=10)['SUPERTd_10_3.0']
    df['atr']=ta.atr(df.high, df.low, df.close, length=14)
    return df

def close_ticker_postion(name,stock_price):
    pos=ib.positions(account=account_no)
    if pos:
        df2=util.df(pos)
        df2['ticker_name']=[cont.symbol for cont in df2['contract']]
        cont=contract_objects[name]
        quant=df2[df2['ticker_name']==name].position.iloc[0]
        print(cont)
        print(quant)
        if quant>0:
            #sell
            # ord=MarketOrder(action='SELL',totalQuantity=quant)
            ord=Order(orderId=ib.client.getReqId(),orderType='MKT',totalQuantity=quantity_,action='SELL',account=account_no,tif=ord_validity)
            ib.placeOrder(cont,ord)
            logging.info('Closing position'+'SELL'+name)
          
        elif quant<0:
            #buy
            # ord=MarketOrder(action='BUY',totalQuantity=quant)
            ord=Order(orderId=ib.client.getReqId(),orderType='MKT',totalQuantity=quantity_,action='BUY',account=account_no,tif=ord_validity)
            ib.placeOrder(cont,ord)
            logging.info('Closing position'+'BUY'+name)



def close_ticker_open_orders(ticker):
    ord=ib.openTrades()
    
   
    if ord:
        df1=util.df(ord)
        print(df1.to_csv('new3.csv'))
        print(df1.columns)
        df1['ticker_name']=[cont.symbol for cont in df1['contract']]
        order_object=df1[df1['ticker_name']==ticker].order.iloc[0]
        print(order_object)
        ib.cancelOrder(order_object)
        logging.info('Canceled current order')



def check_market_order_placed(name):
    ord=ib.reqAllOpenOrders()

    if ord:
        ord_df=pd.DataFrame(ord)
        print(ord_df)
        print(type(ord_df))
        # ord_df.to_csv('order_list.csv')
        ord_df['name']=[c['localSymbol'] for c in list(ord_df['contract'])]
        ord_df['ord_type']=[c['orderType']for c in list(ord_df['order'])]
        a=ord_df[(ord_df['name']==name) & (ord_df['ord_type']=='MKT') ]
        print(a)
        if a.empty:
            return True

        else:
            return False
    else:
        return True



def trade_sell_stocks(stock_name,stock_price,stop_price): #closing_price, quantitys=1  ????


    #market order
    global current_balance
    #market order
    contract = contract_objects[stock_name]
    # ord=MarketOrder(action='SELL',totalQuantity=1,AccountValue=account_no)
    if check_market_order_placed(stock_name):
       
        ord=Order(orderId=ib.client.getReqId(),orderType='MKT',totalQuantity=quantity_,action='SELL',account=account_no,tif=ord_validity)
        trade=ib.placeOrder(contract,ord)
        ib.sleep(1)
        logging.info(trade)
        logging.info('Placed market sell order')


    else:
        logging.info('market order already placed')
        print('market order already placed')
        return 0






def trade_buy_stocks(stock_name,stock_price,stop_price):


    #market order
    contract = contract_objects[stock_name]
    # ord=MarketOrder(action='BUY',totalQuantity=1)
    if check_market_order_placed(stock_name):
        ord=Order(orderId=ib.client.getReqId(),orderType='MKT',totalQuantity=quantity_,action='BUY',account=account_no,tif=ord_validity)
        trade=ib.placeOrder(contract,ord)
        ib.sleep(1)
        logging.info(trade)
        logging.info('Placed market buy order')
  
    else:
        logging.info('market order already placed')
        print('market order already placed')
        return 0        


def macd_xover_refresh(macd,ticker):
    global macd_xover
    if macd['MACD'].iloc[-1].squeeze()>macd['Signal'].iloc[-1].squeeze():
        macd_xover[ticker]="bullish"
    elif macd['MACD'].iloc[-1].squeeze()<macd['Signal'].iloc[-1].squeeze():
        macd_xover[ticker]="bearish"
    print("*****************************************")


def renkoOperation(ticker,last_price): 
    global renko_param           
    if renko_param[ticker]["upper_limit"] == None:
        renko_param[ticker]["upper_limit"] = float(last_price) + renko_param[ticker]["brick_size"]
        renko_param[ticker]["lower_limit"] = float(last_price) - renko_param[ticker]["brick_size"]
    if float(last_price) > renko_param[ticker]["upper_limit"]:
        gap = (float(last_price - renko_param[ticker]["upper_limit"]))//renko_param[ticker]["brick_size"]
        renko_param[ticker]["lower_limit"] = renko_param[ticker]["upper_limit"] + (gap*renko_param[ticker]["brick_size"]) - renko_param[ticker]["brick_size"]
        renko_param[ticker]["upper_limit"] = renko_param[ticker]["upper_limit"] + ((1+gap)*renko_param[ticker]["brick_size"])
        renko_param[ticker]["brick"] = max(1,renko_param[ticker]["brick"]+(1+gap))
    if float(last_price) < renko_param[ticker]["lower_limit"]:
        gap = (renko_param[ticker]["lower_limit"] - float(last_price))//renko_param[ticker]["brick_size"]
        renko_param[ticker]["upper_limit"] = renko_param[ticker]["lower_limit"] - (gap*renko_param[ticker]["brick_size"]) + renko_param[ticker]["brick_size"]
        renko_param[ticker]["lower_limit"] = renko_param[ticker]["lower_limit"] - ((1+gap)*renko_param[ticker]["brick_size"])
        renko_param[ticker]["brick"] = min(-1,renko_param[ticker]["brick"]-(1+gap))
    print(f"{ticker}: brick number = {renko_param[ticker]['brick']},last price ={last_price}, upper bound ={renko_param[ticker]['upper_limit']}, lower bound ={renko_param[ticker]['lower_limit']}")



def pending_tick_handler(t):
    global latest_price
    t=list(t)[0]
    times=t.time.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)
    name=t.contract.symbol 
    price=t.last if t.last else 0
    latest_price[name]=price
    # print(name,times,price)
    renkoOperation(name,price)









def start():
    for ticker in tickers:
        cont=contract_objects[ticker]
        bars =ib.reqHistoricalData(cont, endDateTime='', durationStr=f'2 D',
        barSizeSetting='1 min', whatToShow='MIDPOINT',useRTH=False,formatDate=1)
        df = util.df(bars)
        print(df)
        df['atr']=ta.atr(df.high,df.low,df.close)
        renko_param[ticker] = {"brick_size":round(df.atr.iloc[-1].squeeze(),2),"upper_limit":None, "lower_limit":None,"brick":0}
        macd_xover[ticker] = None
        latest_price[ticker]=df.close.iloc[-1]
    print(macd_xover ,renko_param ) 

logging.info('Strategy started')
current_time=datetime.datetime.now()
print(current_time)

print(datetime.datetime.now())

start_time=datetime.datetime(current_time.year,current_time.month,current_time.day,start_hour,start_min)
end_time=datetime.datetime(current_time.year,current_time.month,current_time.day,end_hour,end_min)
print(start_time)
print(end_time)

logging.info('Checking if start time has been reached')
while start_time>datetime.datetime.now():
    print(datetime.datetime.now())
    time.sleep(1)

start()


for tick in tickers:
    contract=contract_objects[tick]
    market_data=ib.reqMktData(contract, "", False, False)
    ib.pendingTickersEvent += pending_tick_handler

ib.newOrderEvent += order_open_handler
ib.orderStatusEvent += order_open_handler
ib.cancelOrderEvent += order_open_handler






async def main():
    while datetime.datetime.now()<end_time:
        now = datetime.datetime.now()
        seconds_until_next_minute = 60 - now.second+1
        print(seconds_until_next_minute)
        # Sleep until the end of the current minute
        await asyncio.sleep(seconds_until_next_minute)

        # Run your function
        await main_strategy_code()
    

asyncio.run(main())
