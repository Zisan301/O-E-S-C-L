from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def _err(ax, g, x, y, yerr, label):
    ax.errorbar(g[x], g[y], yerr=g[yerr], marker='o', capsize=3, linewidth=1.5, label=label)

def plot_day8_gmi_vs_nu(df: pd.DataFrame, path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(8.6,5.2))
    for s,g in df.groupby('scenario_group'):
        _err(ax, g.sort_values('pcs_nu'), 'pcs_nu','gmi_mean','gmi_ci95', s)
    ax.set_xlabel('PCS shaping coefficient, nu'); ax.set_ylabel('GMI (bits/symbol)'); ax.set_title('C/S/C+S: GMI vs PCS coefficient')
    ax.grid(True, linewidth=.3, alpha=.55); ax.legend(fontsize=8); fig.tight_layout(); fig.savefig(path,dpi=300); plt.close(fig); return path

def plot_day8_rate_gain(df: pd.DataFrame, path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(8.6,5.2))
    for s,g in df.groupby('scenario_group'):
        _err(ax, g.sort_values('pcs_nu'), 'pcs_nu','rate_gain_mean','rate_gain_ci95', s)
    ax.axhline(0, linewidth=1); ax.set_xlabel('PCS shaping coefficient, nu'); ax.set_ylabel('Rate gain (Tb/s/channel)'); ax.set_title('Paired PCS rate gain over uniform')
    ax.grid(True, linewidth=.3, alpha=.55); ax.legend(fontsize=8); fig.tight_layout(); fig.savefig(path,dpi=300); plt.close(fig); return path

def plot_day8_ber(df: pd.DataFrame, path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(8.6,5.2))
    for s,g in df.groupby('scenario_group'):
        g=g.sort_values('pcs_nu'); ax.errorbar(g['pcs_nu'], np.maximum(g['ber_mean'],1e-10), yerr=g['ber_ci95'], marker='o', capsize=3, linewidth=1.5, label=s)
    ax.set_yscale('log'); ax.set_xlabel('PCS shaping coefficient, nu'); ax.set_ylabel('BER'); ax.set_title('BER at selected operating points')
    ax.grid(True, which='both', linewidth=.3, alpha=.55); ax.legend(fontsize=8); fig.tight_layout(); fig.savefig(path,dpi=300); plt.close(fig); return path

def plot_day8_heatmap(df: pd.DataFrame, path: Path) -> Path:
    pivot=df.pivot_table(index='scenario_group', columns='spans', values='best_gmi_gain', aggfunc='mean')
    fig,ax=plt.subplots(figsize=(7.4,3.8)); data=pivot.to_numpy(float); im=ax.imshow(data, aspect='auto')
    ax.set_xticks(range(len(pivot.columns))); ax.set_xticklabels([str(c) for c in pivot.columns]); ax.set_yticks(range(len(pivot.index))); ax.set_yticklabels(list(pivot.index)); ax.set_xlabel('Span count'); ax.set_title('Best PCS GMI gain by scenario/span')
    fig.colorbar(im, ax=ax).set_label('GMI gain');
    for i in range(data.shape[0]):
        for j in range(data.shape[1]): ax.text(j,i,f'{data[i,j]:.3f}',ha='center',va='center',fontsize=8)
    fig.tight_layout(); fig.savefig(path,dpi=300); plt.close(fig); return path

def plot_day8_aggregate_rate(df: pd.DataFrame, path: Path) -> Path:
    fig,ax=plt.subplots(figsize=(8,4.5)); g=df.sort_values('aggregate_rate_gain_mean',ascending=False); ax.bar(g['scenario_group'],g['aggregate_rate_gain_mean'])
    ax.set_ylabel('Aggregate rate gain (Tb/s)'); ax.set_title('Aggregate PCS gain by scenario'); ax.grid(True, axis='y', linewidth=.3, alpha=.55); fig.tight_layout(); fig.savefig(path,dpi=300); plt.close(fig); return path
