from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Tuple
import textwrap
import numpy as np
import pandas as pd
from .constellation import sample_symbols
from .day5_waveform import waveform_ssfm_channel
from .gmi_exact import bit_metric_gmi_awgn, ber_from_decision, estimate_noise_variance_from_decisions
from .utils import ensure_dir
from .day8_plots import plot_day8_gmi_vs_nu, plot_day8_rate_gain, plot_day8_ber, plot_day8_heatmap, plot_day8_aggregate_rate

def _net_rate(gmi: float, cfg: Dict) -> float:
    return float(gmi*float(cfg['simulation']['baud_rate_gbaud'])*1e9*int(cfg['fiber']['polarization_modes'])/1.20/1e12)

def _metrics(tx, tx_idx, rx, priors, cfg):
    nv=max(estimate_noise_variance_from_decisions(rx,tx), float(cfg['day5']['llr_noise_floor']))
    gmi,ngmi=bit_metric_gmi_awgn(tx_indices=tx_idx, rx_symbols=rx, noise_var=nv, priors=priors, max_samples=int(cfg['day5']['gmi_monte_carlo_limit']))
    ber=ber_from_decision(tx_idx,rx)
    gsnr=10*np.log10(float(np.mean(np.abs(tx)**2))/max(float(np.mean(np.abs(rx-tx)**2)),1e-15))
    return {'gmi':float(gmi),'ngmi':float(ngmi),'ber':float(ber),'gsnr_db':float(gsnr),'rate_tbps':_net_rate(gmi,cfg)}

def _ci(df, keys):
    rows=[]
    for kv,g in df.groupby(keys):
        if not isinstance(kv,tuple): kv=(kv,)
        row=dict(zip(keys,kv)); row['n_seeds']=int(g['seed'].nunique())
        for m in ['gmi','ngmi','ber','gsnr_db','rate_tbps','rate_tbps_per_channel']:
            if m not in g: continue
            v=g[m].astype(float).to_numpy(); sd=float(np.std(v,ddof=1)) if len(v)>1 else 0.0
            row[f'{m}_mean']=float(np.mean(v)); row[f'{m}_std']=sd; row[f'{m}_ci95']=float(1.96*sd/np.sqrt(max(len(v),1)))
        rows.append(row)
    return pd.DataFrame(rows)

def _scenario_bands(s): return ['C','S'] if s=='C+S' else [s]

def _stress(cfg, scenario):
    st=dict(cfg['day8']['stress'])
    if scenario=='C+S' and bool(cfg['day8']['cs_interband_penalty']['enabled']):
        p=cfg['day8']['cs_interband_penalty']; st['name']=st['name']+'_cs_penalty'; st['noise']*=float(p['noise_multiplier']); st['nonlinear']*=float(p['nonlinear_multiplier']); st['implementation']*=float(p['implementation_multiplier'])
    return st

def _run_one(seed, scenario, band, spans, power, nu, cfg):
    rng=np.random.default_rng(int(cfg['day8']['seed'])+seed*1000000+int((power+100)*1000)+spans*100+int(nu*10000)+(11 if band=='S' else 5)+(101 if scenario=='C+S' else 0))
    shaped=nu>0; tx,idx,priors=sample_symbols(int(cfg['day8']['symbols']), shaped=shaped, nu=nu, rng=rng); st=_stress(cfg,scenario)
    res=waveform_ssfm_channel(tx,idx,priors,cfg,band,int(spans),float(power),st,rng)
    m=_metrics(res.tx_symbols_aligned,res.tx_indices_aligned,res.rx_symbols,res.priors,cfg)
    if scenario=='C+S': m['gsnr_db']-=float(cfg['day8']['cs_interband_penalty']['gsnr_penalty_db'])
    return {'seed':seed,'scenario_group':scenario,'band':band,'spans':spans,'launch_power_dbm':power,'pcs_nu':nu,'shaped':shaped,'stress_name':st['name'],'display_name':'PCS raw' if shaped else 'Uniform raw','scenario':'pcs_raw' if shaped else 'uniform_raw',**m}

def _run_grid(cfg):
    rows=[]; d=cfg['day8']
    for scenario in d['scenarios']:
        for band in _scenario_bands(scenario):
            for seed in map(int,d['seeds']):
                for spans in map(int,d['spans_grid']):
                    for power in map(float,d['launch_power_grid']):
                        for nu in map(float,d['pcs_nu_grid']): rows.append(_run_one(seed,scenario,band,spans,power,nu,cfg))
    return pd.DataFrame(rows)

def _scenario_seed(raw):
    keys=['seed','scenario_group','spans','launch_power_dbm','pcs_nu','shaped','stress_name','display_name','scenario']
    rows=[]
    for kv,g in raw.groupby(keys):
        row=dict(zip(keys,kv)); row['n_bands']=g['band'].nunique(); row['bands']='+'.join(sorted(g['band'].unique()))
        for m in ['gmi','ngmi','ber','gsnr_db']: row[m]=float(g[m].mean())
        row['rate_tbps']=float(g['rate_tbps'].sum()); row['rate_tbps_per_channel']=float(g['rate_tbps'].mean())
        rows.append(row)
    return pd.DataFrame(rows)

def _paired(seed_df):
    rows=[]; uniform=seed_df[(seed_df.scenario=='uniform_raw')&(seed_df.pcs_nu==0.0)]
    for (scenario,spans,power),base in uniform.groupby(['scenario_group','spans','launch_power_dbm']):
        for nu in sorted(v for v in seed_df.pcs_nu.unique() if v>0):
            pcs=seed_df[(seed_df.scenario_group==scenario)&(seed_df.spans==spans)&(seed_df.launch_power_dbm==power)&(seed_df.scenario=='pcs_raw')&(seed_df.pcs_nu==nu)]
            mg=pcs.merge(base[['seed','gmi','ngmi','ber','gsnr_db','rate_tbps','rate_tbps_per_channel']],on='seed',suffixes=('_pcs','_uniform'))
            if mg.empty: continue
            def st(p,u,name):
                d=mg[p].astype(float)-mg[u].astype(float); sd=float(np.std(d,ddof=1)) if len(d)>1 else 0.0
                return {f'{name}_mean':float(d.mean()),f'{name}_std':sd,f'{name}_ci95':float(1.96*sd/np.sqrt(max(len(d),1)))}
            row={'scenario_group':scenario,'spans':int(spans),'launch_power_dbm':float(power),'pcs_nu':float(nu),'n_pairs':len(mg)}
            row.update(st('gmi_pcs','gmi_uniform','gmi_gain')); row.update(st('ngmi_pcs','ngmi_uniform','ngmi_gain')); row.update(st('ber_pcs','ber_uniform','ber_delta')); row.update(st('gsnr_db_pcs','gsnr_db_uniform','gsnr_delta')); row.update(st('rate_tbps_pcs','rate_tbps_uniform','aggregate_rate_gain')); row.update(st('rate_tbps_per_channel_pcs','rate_tbps_per_channel_uniform','rate_gain'))
            rows.append(row)
    return pd.DataFrame(rows)

def _non_sat(row,cfg):
    d=cfg['day8']; return bool(float(d['target_gmi_min'])<=row.gmi_mean<=float(d['target_gmi_max']) and float(d['target_ngmi_min'])<=row.ngmi_mean<=float(d['target_ngmi_max']) and float(d['target_ber_min'])<=max(row.ber_mean,1e-12)<=float(d['target_ber_max']))

def _accept(ci,gain,cfg):
    rows=[]; d=cfg['day8']
    for scenario,g in gain.groupby('scenario_group'):
        b=g.sort_values('gmi_gain_mean',ascending=False).iloc[0]; nu=float(b.pcs_nu); spans=int(b.spans); power=float(b.launch_power_dbm)
        pcs=ci[(ci.scenario_group==scenario)&(ci.spans==spans)&(ci.launch_power_dbm==power)&(ci.pcs_nu==nu)&(ci.scenario=='pcs_raw')].iloc[0]
        uni=ci[(ci.scenario_group==scenario)&(ci.spans==spans)&(ci.launch_power_dbm==power)&(ci.pcs_nu==0.0)&(ci.scenario=='uniform_raw')].iloc[0]
        passes=bool(b.gmi_gain_mean>=float(d['min_gmi_gain']) and b.ngmi_gain_mean>=float(d['min_ngmi_gain']) and b.rate_gain_mean>=float(d['min_rate_gain_tbps_per_channel']) and b.gmi_gain_mean>b.gmi_gain_ci95 and b.ngmi_gain_mean>b.ngmi_gain_ci95 and b.rate_gain_mean>b.rate_gain_ci95 and pcs.ber_mean<=float(d['max_ber']) and (not d['require_non_saturated'] or (_non_sat(pcs,cfg) and _non_sat(uni,cfg))))
        rows.append({'scenario_group':scenario,'passes_q3_band_gate':passes,'best_pcs_nu':nu,'spans':spans,'launch_power_dbm':power,'gmi_gain_mean':b.gmi_gain_mean,'gmi_gain_ci95':b.gmi_gain_ci95,'ngmi_gain_mean':b.ngmi_gain_mean,'ngmi_gain_ci95':b.ngmi_gain_ci95,'rate_gain_mean':b.rate_gain_mean,'rate_gain_ci95':b.rate_gain_ci95,'aggregate_rate_gain_mean':b.aggregate_rate_gain_mean,'aggregate_rate_gain_ci95':b.aggregate_rate_gain_ci95,'ber_delta_mean':b.ber_delta_mean,'ber_delta_ci95':b.ber_delta_ci95,'non_saturated':_non_sat(pcs,cfg) and _non_sat(uni,cfg)})
    return pd.DataFrame(rows)

def _best_span(gain):
    return pd.DataFrame([{'scenario_group':s,'spans':int(sp),'best_pcs_nu':float(g.sort_values('gmi_gain_mean',ascending=False).iloc[0].pcs_nu),'best_launch_power_dbm':float(g.sort_values('gmi_gain_mean',ascending=False).iloc[0].launch_power_dbm),'best_gmi_gain':float(g.sort_values('gmi_gain_mean',ascending=False).iloc[0].gmi_gain_mean),'best_rate_gain':float(g.sort_values('gmi_gain_mean',ascending=False).iloc[0].rate_gain_mean),'best_aggregate_rate_gain':float(g.sort_values('gmi_gain_mean',ascending=False).iloc[0].aggregate_rate_gain_mean)} for (s,sp),g in gain.groupby(['scenario_group','spans'])])

def _selected(ci, acc):
    parts=[]
    for _,a in acc.iterrows():
        parts.append(ci[(ci.scenario_group==a.scenario_group)&(ci.spans==a.spans)&(ci.launch_power_dbm==a.launch_power_dbm)&(ci.scenario=='pcs_raw')])
    return pd.concat(parts,ignore_index=True)

def _write(cfg, ci, gain, acc, best_span, figs):
    rd=ensure_dir(cfg['output']['reports']); report=rd/'day8_q3_band_comparison_report.md'; ar=rd/'day8_q3_acceptance_report.md'; tex=rd/'day8_latex_journal_results_snippet.tex'
    report.write_text('# Day-8 Q3 C/S/C+S Band Comparison Report\n\nThis run upgrades the single C-band conference result into a comparative C, S, and C+S journal-style study.\n\n## Acceptance summary\n\n'+acc.round(6).to_markdown(index=False)+'\n\n## Best PCS gain by span\n\n'+best_span.round(6).to_markdown(index=False)+'\n\n## Figures\n'+'\n'.join(f'- `{p}`' for p in figs)+'\n\nImportant limitation: C+S uses a simplified lumped inter-band penalty, not full Raman-calibrated WDM.\n')
    passed=int(acc.passes_q3_band_gate.sum()); claim='PCS gains are band- and operating-region-dependent; accepted scenarios can be used for a Q3 journal claim.' if passed>=2 else ('Only one scenario passed; use other scenarios as weak/negative comparative evidence.' if passed==1 else 'Q3 claim not ready; retune band stress model.')
    ar.write_text(f'# Day-8 Q3 Acceptance Report\n\nPassed scenarios: {passed}/{len(acc)}\n\nRecommended claim: {claim}\n\n'+acc.round(6).to_markdown(index=False)+'\n')
    best=acc.sort_values('gmi_gain_mean',ascending=False).iloc[0]
    tex.write_text(f"""\\subsection{{C/S/C+S Band Comparison}}
Day-8 extends the focused C-band PCS confirmation to C, S, and combined C+S scenarios. The strongest scenario is {best.scenario_group}, with $\\nu={best.best_pcs_nu:.2f}$, {int(best.spans)} spans, and {best.launch_power_dbm:.1f} dBm/channel. It gives a paired GMI gain of {best.gmi_gain_mean:.4f}$\\pm${best.gmi_gain_ci95:.4f} bits/symbol and a rate gain of {best.rate_gain_mean:.4f}$\\pm${best.rate_gain_ci95:.4f} Tb/s/channel. The C+S case uses a simplified lumped inter-band penalty and is not claimed as full Raman-calibrated WDM validation.
""")
    return report, ar, tex

def run_day8_q3_band_comparison(cfg: Dict) -> Dict:
    td=ensure_dir(cfg['output']['tables']); fd=ensure_dir(cfg['output']['figures'])
    raw=_run_grid(cfg); seed=_scenario_seed(raw); ci=_ci(seed,['scenario_group','spans','launch_power_dbm','pcs_nu','shaped','stress_name','display_name','scenario','n_bands','bands']); gain=_paired(seed); acc=_accept(ci,gain,cfg); bs=_best_span(gain); sel=_selected(ci,acc)
    raw.to_csv(td/'day8_raw_band_metrics.csv',index=False); seed.to_csv(td/'day8_scenario_seed_metrics.csv',index=False); ci.to_csv(td/'day8_ci_metrics.csv',index=False); gain.to_csv(td/'day8_paired_pcs_gains.csv',index=False); acc.to_csv(td/'day8_acceptance_summary.csv',index=False); bs.to_csv(td/'day8_best_gain_by_span.csv',index=False)
    figs=[plot_day8_gmi_vs_nu(sel,fd/'fig_day8_gmi_vs_nu_c_s_cs.png'), plot_day8_rate_gain(gain,fd/'fig_day8_rate_gain_vs_nu.png'), plot_day8_ber(sel,fd/'fig_day8_ber_vs_nu_c_s_cs.png'), plot_day8_heatmap(bs,fd/'fig_day8_gain_heatmap_scenario_span.png'), plot_day8_aggregate_rate(acc,fd/'fig_day8_aggregate_rate_gain.png')]
    rp,ap,tex=_write(cfg,ci,gain,acc,bs,figs)
    return {'report_path':str(rp),'acceptance_report_path':str(ap),'latex_snippet_path':str(tex),'figure_paths':[str(p) for p in figs],'ci_csv':str(td/'day8_ci_metrics.csv'),'gain_csv':str(td/'day8_paired_pcs_gains.csv'),'acceptance_csv':str(td/'day8_acceptance_summary.csv'),'best_gain_by_span_csv':str(td/'day8_best_gain_by_span.csv')}
