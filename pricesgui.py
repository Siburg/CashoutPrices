import pickle
from tkinter import *
from decimal import Decimal, ROUND_HALF_UP


class WeldedPoint:
    def __init__(self, name, distance, wptype="Physical"):
        self.name = name
        self.distance = distance
        self.wptype = wptype
        # assume at this stage we do not need welded point size for anything
        # no other attributes needed either

    def __repr__(self):
        return "%s %s Welded Point at %s km" % (self.name, self.wptype, str(self.distance))


def amp_plus_mbpa(amp, mbpa):
    dec_amp = Decimal(str(amp))
    dec_mbpa = Decimal(str(mbpa))
    adjusted_amp = dec_amp * (Decimal("1") + dec_mbpa * Decimal("0.01"))
    return adjusted_amp.quantize(Decimal('.000001'), rounding=ROUND_HALF_UP)


def amp_minus_mspa(amp, mspa):
    dec_amp = Decimal(str(amp))
    dec_mspa = Decimal(str(mspa))
    adjusted_amp = dec_amp * (Decimal("1") - dec_mspa * Decimal("0.01"))
    return adjusted_amp.quantize(Decimal('.000001'), rounding=ROUND_HALF_UP)


def marginal_buy_price(amp, mbpa, highest_call=Decimal("0")):
    # used for Pipeline Sell, which is a buy for a Welded Party
    # amp = Average Market Price
    # mbpa = Marginal Buy Price Adjustment percentage: enter 3% as 3
    # highest_call = highest Balancing Gas Call price for delivery on the Day
    # highest_call is optional; if not provided it uses 0
    # all paramaters can be provided as floats or as decimals
    # in case they are floats, they are first converted into decimals below
    # note that these conversions are harmless if they apply to decimals to start with
    adjusted_amp = amp_plus_mbpa(amp, mbpa)
    dec_hi_call = Decimal(str(highest_call))
    if adjusted_amp > dec_hi_call:
        return adjusted_amp
    else:
        return dec_hi_call


def marginal_sell_price(amp, mspa, lowest_put=Decimal("Infinity")):
    # used for Pipeline Buy, which is a sell for a Welded Party
    # amp = Average Market Price
    # mspa = Marginal Sell Price Adjustment expressed as a number: enter 3% as 0.03
    # lowest_put = lowest Balancing Gas Put price for delivery on the Day
    # lowest_put is optional; if not provided it uses infinity in order to ensure
    # that it is not used in the calculation
    # all paramaters can be provided as floats or as decimals
    # in case they are floats, they are first converted into decimals below
    # note that these conversions are harmless if they apply to decimals to start with
    adjusted_amp = amp_minus_mspa(amp, mspa)
    dec_lo_put = Decimal(str(lowest_put))
    if adjusted_amp < dec_lo_put:
        return adjusted_amp
    else:
        return dec_lo_put   # no need to round in this case

"""########################################
def cash_out_sell_price(msp, wp, trading_fee, tariff1, tariff2=Decimal('0')):
    # assume that all input parameters (except wp) are already in Decimal format
    # if not, then conversions to decimal should be added below
    travel = Decimal(abs(wp.distance - PAYBACK_DISTANCE)).quantize(Decimal('.001'))
    tariff1_part = (travel * tariff1).quantize(Decimal('.000001'), rounding=ROUND_HALF_UP)
    raw_price = msp - trading_fee - tariff1_part # tariff2 is not currently in calculation
    if raw_price < MINIMUM_SELL_PRICE:
        return MINIMUM_SELL_PRICE
    else:
        return raw_price

def cash_out_buy_price(mbp, wp, trading_fee, tariff1, tariff2):
    # assume that all input parameters (except wp) are already in Decimal format
    # if not, then conversions to decimal should be added below
    travel = Decimal(abs(wp.distance - PAYBACK_DISTANCE)).quantize(Decimal('.001'))
    tariff1_part = (travel * tariff1).quantize(Decimal('.000001'), rounding=ROUND_HALF_UP)
    raw_price = mbp + trading_fee + tariff1_part
    if wp.wptype == "Physical":
        return raw_price + tariff2
    else:
        return raw_price
"""


def calculate_marginal():
    last_amp = amp.get()
    last_mbpa = mbpa.get()
    last_mspa = mspa.get()
    amp_plus.set(amp_plus_mbpa(last_amp, last_mbpa))
    amp_minus.set(amp_minus_mspa(last_amp, last_mspa))
    last_hicall = hicall.get()
    last_loput = loput.get()
    mbp.set(marginal_buy_price(last_amp, last_mbpa, last_hicall))
    msp.set(marginal_sell_price(last_amp, last_mspa, last_loput))
    return


def calculate_cashout():
    selected = wpselect.curselection()[0]
    travel = abs(Decimal(weldedpoints[selected].distance) - Decimal(PAYBACK_DISTANCE))
    tariff1_part = (travel * tariff1).quantize(Decimal('.000001'), rounding=ROUND_HALF_UP)
    if weldedpoints[selected].wptype == "Physical":
        tariff2_part_buy = tariff2
        transmission_price_buy = tariff1_part + tariff2_part_buy
    else:
        tariff2_part_buy = "N/A"
        transmission_price_buy = tariff1_part
    cash_out_buy_price = Decimal(str(mbp.get())) + trading_fee + transmission_price_buy
    tariff2_part_sell = "N/A"
    transmission_price_sell = tariff1_part
    cash_out_sell_price = Decimal(msp.get()) - trading_fee - transmission_price_sell
    if cash_out_sell_price < MINIMUM_SELL_PRICE:
        cash_out_sell_price = MINIMUM_SELL_PRICE

    print(travel, tariff1_part, transmission_price_buy, transmission_price_sell, cash_out_buy_price)
    return


MINIMUM_SELL_PRICE = Decimal("0.01")
PAYBACK_DISTANCE = "65.3"
trading_fee = Decimal("0.10")
tariff1 = Decimal("0.001578")
tariff2 = Decimal("0.076779")
last_mbpa = Decimal("3.00")
last_mspa = Decimal("3.00")
last_amp = Decimal("8.80")
last_hicall = Decimal("8.00")
last_loput = Decimal("2.00")

with open("/home/jelle/prices.pickle", "rb") as picklefile:
    weldedpoints = pickle.load(picklefile)

wpnames = []
for wp in weldedpoints:
    wpnames.append(wp.name)


mainwin = Tk()
mainwin.title("prices calculation")

margframe = Frame(mainwin, bd=3, relief=SUNKEN)
margframe.pack(side=TOP, fill=BOTH, expand=1)
margframe.bind_all("<Return>", lambda event: calculate_marginal())

amp = StringVar(margframe)
mbpa = StringVar(margframe)
mspa = StringVar(margframe)
amp_plus = StringVar(margframe)
amp_minus = StringVar(margframe)
hicall = StringVar(margframe)
loput = StringVar(margframe)
mbp = StringVar(margframe)
msp = StringVar(margframe)

margframetext = Label(margframe, text="Determine Marginal Buy/Sell Prices (applicable to all Welded Points)")
margframetext.grid(row=0, column=0, columnspan=6)

amptext = Label(margframe, text="Average\nMarket\nPrice")
amptext.grid(row=2, column=0)
ampentry = Entry(margframe, textvariable=amp, width=10)
ampentry.grid(row=2, column=1)
mbpatext = Label(margframe, text='marginal\nbuy price\nadjustment')
mbpatext.grid(row=1, column=2)
mbpaentry = Entry(margframe, textvariable=mbpa, width=5)
mbpaentry.grid(row=1, column=3)
mbpaendtext = Label(margframe, text="%")
mbpaendtext.grid(row=1, column=4)
amp_plus_text = Label(margframe, text="AMP + adj")
amp_plus_text.grid(row=1, column=5)
amp_plus_result = Label(margframe, textvariable=amp_plus)
amp_plus_result.grid(row=1, column=6)
mspatext = Label(margframe, text='marginal\nsell price\nadjustment')
mspatext.grid(row=3, column=2)
mspaentry = Entry(margframe, textvariable=mspa, width=5)
mspaentry.grid(row=3, column=3)
mspaendtext = Label(margframe, text="%")
mspaendtext.grid(row=3, column=4)
amp_minus_text = Label(margframe, text="AMP - adj")
amp_minus_text.grid(row=3, column=5)
amp_minus_result = Label(margframe, textvariable=amp_minus)
amp_minus_result.grid(row=3, column=6)
hicalltext = Label(margframe, text="highest\nBG Call")
hicalltext.grid(row=1, column=7)
hicallentry = Entry(margframe, textvariable=hicall, width=6)
hicallentry.grid(row=1, column=8)
loputtext = Label(margframe, text="lowest\nBG Put")
loputtext.grid(row=3, column=7)
loputentry = Entry(margframe, textvariable=loput, width=6)
loputentry.grid(row=3, column=8)
mbp_result_text = Label(margframe, text="Marginal Buy\nPrice (for)\nPipeline Sell)")
mbp_result_text.grid(row=1, column=9)
mbp_result = Label(margframe, textvariable=mbp, width=10)
mbp_result.grid(row=1, column=10)
msp_result_text = Label(margframe, text="Marginal Sell\nPrice (for)\nPipeline Buy)")
msp_result_text.grid(row=3, column=9)
msp_result = Label(margframe, textvariable=msp, width=10)
msp_result.grid(row=3, column=10)


calcbtn = Button(margframe, text="Calculate", command=lambda: calculate_marginal())
calcbtn.grid(row=4, column=6)

amp.set(last_amp)
mbpa.set(last_mbpa)
mspa.set(last_mspa)
amp_plus.set(amp_plus_mbpa(last_amp, last_mbpa))
amp_minus.set(amp_minus_mspa(last_amp, last_mspa))
hicall.set(last_hicall)
loput.set(last_loput)
mbp.set(marginal_buy_price(last_amp, last_mbpa, last_hicall))
msp.set(marginal_sell_price(last_amp, last_mspa, last_loput))

wpframe = Frame(mainwin)
wpframe.pack(side=TOP, fill=BOTH, expand=1)

wpframetext = Label(wpframe, text="Calculate Cash-Out Buy/Sell Prices for a specific Welded Point")
wpframetext.grid(row=0, column=0, columnspan=6)


wptext = Label(wpframe, text="Welded Point")
wptext.grid(row=1, column=0)
scrollbar = Scrollbar(wpframe, orient=VERTICAL)
wpselect = Listbox(wpframe, width=20, height=6, selectmode=SINGLE, yscrollcommand=scrollbar.set)
scrollbar.config(command=wpselect.yview)
wpselect.grid(row=2, column=0)
scrollbar.grid(row=2, column=1, sticky="ns")
for wpname in wpnames:
    wpselect.insert(END, wpname)
wpselect.bind("<<ListboxSelect>>", lambda event: calculate_cashout())


distancetext = Label(wpframe, text="Distance from\nPayback Point")
distancetext.grid(row=1, column=2)


mainwin.mainloop()
