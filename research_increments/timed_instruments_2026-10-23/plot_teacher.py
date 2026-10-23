from pathlib import Path
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
ROOT=Path(__file__).resolve().parent
public=json.loads((ROOT/"RESULTS.json").read_text())
table=public["teacher_pilot"]
assert table["raw_audited_cases"]==192 and table["graphs"]==64
arms=["E_T_V2","E_T_HISTORY","E_L_V2"]
labels=["Current-only\nteacher","History\nteacher","Public ledger\nexpert"]
colors=["#526F8F","#A8733A","#3A897F"]
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.spines.top":False,"axes.spines.right":False,"pdf.fonttype":42})
fig,axes=plt.subplots(1,3,figsize=(11.8,3.6),gridspec_kw={"width_ratios":[1,1,1.15]})
for ax,layer,title in zip(axes[:2],["ALL","CERT_FEASIBLE"],["All registered graphs (n=64)","Reference-feasible graphs (n=40)"]):
 rows=[next(r for r in table["cells"] if r["expert_or_arm"]==a and r["stratum"]==layer and r["mode"]=="main") for a in arms]
 y=np.array([r["S"]/r["N"] for r in rows]);lo=np.array([r["wilson95"][0] for r in rows]);hi=np.array([r["wilson95"][1] for r in rows])
 ax.bar(range(3),y,color=colors,width=.6,zorder=2)
 ax.errorbar(range(3),y,yerr=np.array([y-lo,hi-y]),fmt="none",ecolor="#263442",capsize=4,zorder=3)
 for x,r in enumerate(rows):ax.text(x,r["wilson95"][1]+.028,f"{r['S']}/{r['N']}",ha="center",fontsize=10)
 ax.set_xticks(range(3),labels);ax.tick_params(axis="x",labelsize=8);ax.set_ylim(0,1.06);ax.set_title(title,fontsize=11,pad=12);ax.set_ylabel("Original task success");ax.yaxis.grid(True,alpha=.16,zorder=0)
ax=axes[2]
rows=[next(r for r in table["paired"] if r["arm_a"]=="E_T_V2" and r["arm_b"]=="E_T_HISTORY" and r["stratum"]==s) for s in ["ALL","CERT_FEASIBLE"]]
for y,r in enumerate(rows):
 lo,hi=r["conservative95"];d=r["difference_b_minus_a"]
 ax.errorbar(d*100,y,xerr=[[100*(d-lo)],[100*(hi-d)]],fmt="o",color="#A8733A",capsize=5,markersize=6)
ax.axvline(0,color="#71808B",lw=1,ls="--");ax.set_yticks([0,1],["All graphs","Reference-feasible"]);ax.set_ylim(1.7,-.7);ax.set_xlim(-15,15);ax.set_xlabel("History minus current-only (pp)");ax.set_title("Paired success difference",fontsize=11,pad=12)
fig.suptitle("History access alone did not change success on this pilot",fontsize=14,y=1.03)
fig.text(.01,-.04,"64 fresh MYA graphs; same scheduler; fixed 0.5 sim-s window. Wilson 95% bars; conservative paired intervals.\nAll failures retained. Feasible n=40 is below the formal gate minimum of 50. This is a scripted CPU pilot, not a learned-method result.",fontsize=9,color="#42515E")
fig.tight_layout(w_pad=2)
for suffix in ("png","pdf","svg"):fig.savefig(ROOT/("teacher_history_pilot."+suffix),dpi=220,bbox_inches="tight")
print("Reproduced figure from published aggregates; no physics or private files")
