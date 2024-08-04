#super trend and ema strategy
#closing greater than daily ema
#super positive in hourly
import pandas as pd
import datetime 
import time
from ib_insync import *
import pandas as pd
import pandas_ta as ta

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




    #stop order
    order = Order()
    order.orderId = ib.client.getReqId()
    order.action = 'BUY'
    order.orderType = "STP"
    order.totalQuantity = quantity_
    order.auxPrice = int(stop_price)
    order.tif = ord_validity
    order.account=account_no

    trade=ib.placeOrder(contract, order)
    ib.sleep(1)
    logging.info(trade)
    logging.info("placed stop order")



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



    #stop order
    order = Order()
    order.orderId = ib.client.getReqId()
    order.action = 'SELL'
    order.orderType = "STP"
    order.totalQuantity = quantity_
    order.auxPrice = int(stop_price)
    order.tif = ord_validity
    order.account=account_no


    trade=ib.placeOrder(contract, order)
    ib.sleep(1)
    logging.info(trade)
    logging.info("placed stop order")



def strategy(hist_df_hourly,hist_df_daily,ticker):
    logging.info('inside strategy')
    print('inside strategy')
    # print(ticker)
    # print(hist_df_hourly)
    # print(hist_df_daily)
    hourly_closing_price=hist_df_hourly.close.iloc[-1]
    buy_condition=hist_df_hourly['super'].iloc[-1]>0 and hist_df_daily['ema'].iloc[-1]<hist_df_hourly['close'].iloc[-1]
    # buy_condition=True
    sell_condition=hist_df_hourly['super'].iloc[-1]<0 and hist_df_daily['ema'].iloc[-1]>hist_df_hourly['close'].iloc[-1]
    # sell_condition=True
    current_balance=int(float([v for v in ib.accountValues(account=account_no) if v.tag == 'AvailableFunds' ][0].value))
    atr_value=hist_df_daily['atr'].iloc[-1]
    print(atr_value)
    logging.info(atr_value)
    if current_balance>hist_df_hourly.close.iloc[-1]:
        if buy_condition:
            logging.info('buy condiiton satisfied')
            trade_buy_stocks(ticker,hourly_closing_price,hourly_closing_price-atr_value)
        elif sell_condition:
            logging.info('sell condition satisfied')
            trade_sell_stocks(ticker,hourly_closing_price,hourly_closing_price+atr_value)
        else :
            logging.info('no condition satisfied')
    else:
        logging.info('we dont have enough money')
        logging.info('current balance is',current_balance,'stock price is ',hist_df_hourly['close'].iloc[-1])


def main_strategy_code():

    print("inside main strategy")
    pos=ib.positions(account=account_no)
    print(pos)
    if len(pos)==0:
        pos_df=pd.DataFrame([])
    else:
        pos_df=util.df(pos)
        pos_df['name']=[cont.symbol for cont in pos_df['contract']]
        pos_df=pos_df[pos_df['position']!=0]
    print(pos_df)
    ord=ib.reqAllOpenOrders()
    if len(ord)==0:
        ord_df=pd.DataFrame([])
    else:
        ord_df=util.df(ord)
        ord_df['name']=[cont.symbol for cont in ord_df['contract']]
    print(ord_df)
    logging.info('Fetched order_df and position_df')

    for ticker in tickers:
        logging.info(ticker)
        print('ticker name is',ticker,'################')
        ticker_contract=contract_objects[ticker]
     

        hist_df_hourly=get_historical_data(ticker_contract,'1 hour','10 D')
        hist_df_daily=get_historical_data(ticker_contract,'1 day','50 D')
        # print(hist_df_hourly)
        # print(hist_df_daily)


        # print(hist_df_hourly.close.iloc[-1])
      
        capital=int(float([v for v in ib.accountValues(account=account_no) if v.tag == 'AvailableFunds' ][0].value))
        print(capital)
        quantity=int((capital/10)/hist_df_hourly.close.iloc[-1])  
        print(quantity)
        logging.info('Checking condition')

        if quantity==0:
            logging.info('we dont have enough money so we cannot trade')
            continue

        if pos_df.empty:
            print('we dont have any position')
            logging.info('we dont have any position')
      
            strategy(hist_df_hourly,hist_df_daily,ticker)


        elif len(pos_df)!=0 and ticker not in pos_df['name'].tolist():
            logging.info('we have some position but current ticker is not in position')
            print('we have some position but current ticker is not in position')
            strategy(hist_df_hourly,hist_df_daily,ticker)
        


        elif len(pos_df)!=0 and ticker in pos_df["name"].tolist():
            logging.info('we have some position and current ticker is in position')
            print('we have some position and current ticker is in position')
            
            if pos_df[pos_df["name"]==ticker]["position"].values[0] == 0:
                logging.info('we have current ticker in position but quantity is 0')
                print('we have current ticker in position but quantity is 0')
                strategy(hist_df_hourly,hist_df_daily,ticker)

            elif pos_df[pos_df["name"]==ticker]["position"].values[0] > 0  :
                logging.info('we have current ticker in position and is long')
                print('we have current ticker in position and is long')
                sell_condition=hist_df_hourly['super'].iloc[-1]<0 and hist_df_daily['ema'].iloc[-1]>hist_df_hourly['close'].iloc[-1]
                # sell_condition=True
                # current_balance=int(float([v for v in ib.accountValues(account=account_no) if v.tag == 'AvailableFunds' ][0].value))
                # if current_balance>hist_df.close.iloc[-1]:
                if sell_condition:
                            hourly_closing_price=hist_df_hourly['close'].iloc[0]
                            atr_value=hist_df_daily['atr'].iloc[-1]
                            print('sell condition satisfied')
                            logging.info('sell condition satisfied')
                            close_ticker_open_orders(ticker)
                            close_ticker_postion(ticker)
                            trade_sell_stocks(ticker,hourly_closing_price+atr_value)
                        
                            
            


            elif pos_df[pos_df["name"]==ticker]["position"].values[0] < 0 :
                print('we have current ticker in position and is short')
                logging.info('we have current ticker in position and is short')
                hourly_closing_price=hist_df_hourly['close'].iloc[0]
                atr_value=hist_df_daily['atr'].iloc[-1]
                buy_condition=hist_df_hourly['super'].iloc[-1]>0 and hist_df_daily['ema'].iloc[-1]<hist_df_hourly['close'].iloc[-1]
                # buy_condition=True
                # current_balance=int(float([v for v in ib.accountValues(account=account_no) if v.tag == 'AvailableFunds' ][0].value))
                # if current_balance>hist_df.close.iloc[-1]:
         
                if buy_condition:
                            print('buy condiiton satisfied')
                            logging.info('buy condiiton satisfied')
                            close_ticker_open_orders(ticker)
                            close_ticker_postion(ticker)
                        
                            trade_buy_stocks(ticker,hourly_closing_price-atr_value)
       






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

logging.info('Starting the main code')

candle_size=60

ib.newOrderEvent += order_open_handler
ib.orderStatusEvent += order_open_handler
ib.cancelOrderEvent += order_open_handler

logging.info('Starting the main code with candle size'+str(candle_size))
while datetime.datetime.now()<end_time:
    main_strategy_code()
    now = datetime.datetime.now()
    print(now)
    seconds_until_next_minute = candle_size - now.second+1
    print(seconds_until_next_minute)
    # Sleep until the end of the current minute
    time.sleep(seconds_until_next_minute)

    # Run your function
    




