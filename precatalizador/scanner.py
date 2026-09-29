#!/usr/bin/env python3
"""Pre-catalyst cross-sector research screen. Curated evidence, live Yahoo quote; no orders."""
import json, os, sys
from datetime import date, datetime, timezone
from pathlib import Path
import yfinance as yf

ROOT=Path(__file__).resolve().parent
TODAY=date.today()
MAX_EVIDENCE_AGE=120 # a company's dated financial snapshot needs manual refresh

def check(row):
    ticker=row['ticker']; stock=yf.Ticker(ticker); info=stock.info
    h=stock.history(period='5mo',auto_adjust=True)
    if len(h)<61:raise ValueError('Insufficient trading history')
    if h.index[-1].date()==TODAY:h=h.iloc[:-1] # avoid unfinished trading session
    if len(h)<60:raise ValueError('Insufficient completed sessions')
    px=info.get('currentPrice') or info.get('regularMarketPrice')
    cap=info.get('marketCap'); unit=info.get('currency')
    if not px or not cap or not unit:raise ValueError('Market price/cap/currency missing')
    # Yahoo .L quotes are often pence, while marketCap is pounds; never convert cap using GBp.
    rates={'USD':1.0,'EUR':float(yf.Ticker('EURUSD=X').history(period='5d')['Close'].iloc[-1]),
           'GBP':float(yf.Ticker('GBPUSD=X').history(period='5d')['Close'].iloc[-1]),
           'SEK':float(yf.Ticker('SEKUSD=X').history(period='5d')['Close'].iloc[-1])}
    if unit not in rates and unit!='GBp':raise ValueError('No verified conversion for '+unit)
    quote_price=px/100 if unit=='GBp' else px
    local_ccy='GBP' if unit=='GBp' else unit
    usd_cap=cap*rates[local_ccy]
    # Pre-event thesis must have a primary dated source for milestone and financials.
    cat=row['catalyst']; start=date.fromisoformat(cat['window_start']); end=date.fromisoformat(cat['window_end'])
    record=date.fromisoformat(row['financial_as_of']); age=(TODAY-record).days
    monthly_burn=row.get('monthly_burn_m_local')
    cash=row.get('cash_m_local'); est=(cash/monthly_burn) if cash is not None and monthly_burn and monthly_burn>0 else None
    months_to_event=max(0,(end-TODAY).days/30.44)
    guidance_until=date.fromisoformat(row['runway_guidance_until']) if row.get('runway_guidance_until') else None
    guidance_margin=((guidance_until-end).days/30.44) if guidance_until else None
    # A calendar-quarter runway statement is approximate: use an explicit window
    # with at least 6 full months strictly beyond the planned event end.
    vol=float(h['Volume'].iloc[-20:].mean()/h['Volume'].iloc[-60:-20].mean())
    change=float(h['Close'].iloc[-1]/h['Close'].iloc[-60]-1)
    quote_range=(.10<=quote_price<=20) if local_ccy in ('EUR','USD') else None
    flags={
       'catalyst_future_verified_window': bool(cat['source_url'] and cat['type'] in ('trial_readout','regulatory_decision','contract_award','commercial_milestone','profit_inflection') and start<=end and end>=TODAY and (end-TODAY).days<=548),
       'cap_300m_3b_usd': 300e6<=usd_cap<=3e9,
       'survives_event_plus_6mo': est is not None and est>=months_to_event+6 and (guidance_margin is None or guidance_margin>=6),
       'no_60session_euphoria': change<1,
       'financial_snapshot_not_stale':0<=age<=MAX_EVIDENCE_AGE,
       'dilution_review_complete':row.get('dilution_status')=='reviewed_no_imminent_financing',
       'business_quality_reviewed':row.get('quality_status')=='reviewed',
    }
    return {'ticker':ticker,'sector':row['sector'],'market':row['market'],'as_of':str(TODAY),
      'cap_usd_m':round(usd_cap/1e6,1),'market_cap_local_m':round(cap/1e6,1),
      'price':round(px,3),'price_currency_unit':unit,'price_0_10_to_20_eur_usd_informational':quote_range,
      'catalyst':cat,'cash_m_local':cash,'monthly_burn_m_local':monthly_burn,
      'runway_est_months':round(est,1) if est else None,'months_to_event_end':round(months_to_event,1),
      'runway_guidance_until':str(guidance_until) if guidance_until else None,'guidance_margin_after_event_months':round(guidance_margin,1) if guidance_margin is not None else None,
      'financial_as_of':str(record),'financial_source_url':row['financial_source_url'],
      'dilution_status':row.get('dilution_status'),'dilution_note':row.get('dilution_note'),
      'quality_status':row.get('quality_status'),'quality_note':row.get('quality_note'),
      'expansion_note':row.get('expansion_note'),
      'volume_ratio_20_vs_previous40':round(vol,2),'return_60sessions_pct':round(change*100,1),
      'last_complete_session':str(h.index[-1].date()), 'flags':flags,
      'review_required':not all(flags.values()),'score':sum(flags.values())}

def main():
    data=json.loads((ROOT/'universe.json').read_text());res=[]
    for row in data:
        try:res.append(check(row))
        except Exception as e:res.append({'ticker':row['ticker'],'error':str(e),'score':0,'review_required':True})
    res.sort(key=lambda x:(x['score'],x.get('cap_usd_m',0)),reverse=True)
    out={'generated_at_utc':datetime.now(timezone.utc).isoformat(),
      'limits':'Curated NON-EXHAUSTIVE universe; dates/financials manually transcribed from primary releases, not auto-discovered. Market Yahoo snapshots can stale. Score is evidence checklist, not chance of x5. No trading signal. Reconfirm current filings and catalyst before action.', 'results':res}
    (ROOT/'scan.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
    for r in res:
        print(f"{r['ticker']:9} {r['score']}/7 {r.get('cap_usd_m','?')}M USD  event={r.get('catalyst',{}).get('window_end')} runway={r.get('runway_est_months')}mo ret60={r.get('return_60sessions_pct')}% missing="+str([k for k,v in r.get('flags',{}).items() if not v])+(' ERROR '+r['error'] if 'error' in r else ''))
if __name__=='__main__':main()
