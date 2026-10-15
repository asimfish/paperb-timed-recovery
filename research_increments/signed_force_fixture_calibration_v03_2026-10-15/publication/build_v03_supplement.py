#!/usr/bin/env python3
"""Add pinned actual V03 evidence to an existing calibration page. No RAW decode."""
from __future__ import annotations
import argparse
import hashlib
import html
import json
from pathlib import Path, PurePosixPath
import re
import shutil

HERE = Path(__file__).resolve().parent
INCREMENT = HERE.parent
NAME = INCREMENT.name
CLOSURE_SHA = '7ef83aaad95068f4da00dbefcf7ee8da7a1e83c2c7b5c0a575a1c60fa8718108'
COLLECTOR_FREEZE_SHA = '29b848d388897fa8c08088e0bde940ec751585e83d308e137a26f99eacaace4f'
READER_FREEZE_SHA = '52d9b5009be016b53905927bcfdcf4a4c5b8eb2b83f110384237734d670fbb1d'
READER_REVIEW_SHA = '5e0fb9eb437f18d42404be4bb279dd2ef3e92e5613ca6a1cad04221e1c47a6f0'
CASES = (
    ('cal_force_c1_stack_processing_off_v03', 'C1 · OFF 对照', '同一堆叠夹具，关闭接触报告'),
    ('cal_force_c0_freefall_v03', 'C0 · 自由落体', '无地面、无第二物体，检查实际重力加速度'),
    ('cal_force_c1_stack_v03', 'C1 · 重力支撑', '0.1 kg 上方物体的支撑力、反作用力与 dt'),
    ('cal_force_c2_rotated_v03', 'C2 · 旋转夹具', '同步旋转夹具和重力，检查世界坐标方向'),
    ('cal_force_c3_actor_order_v03', 'C3 · 创建顺序', '改变创建顺序，检查世界力表示；隐藏顺序仍未知'),
    ('cal_force_c4_mass_v03', 'C4 · 质量倍增', '上方质量 0.1 → 0.2 kg，其他物理参数不变'),
)
START = '<!-- V03_ACTUAL_SUPPLEMENT_BEGIN -->'
END = '<!-- V03_ACTUAL_SUPPLEMENT_END -->'


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def bound_json(path, expected):
    if sha(path) != expected:
        raise ValueError(f'SOURCE_SHA_MISMATCH: {path}')
    return json.loads(Path(path).read_text())


def relative(value):
    p = PurePosixPath(value)
    if p.is_absolute() or '..' in p.parts or not p.parts or not all(re.fullmatch(r'[A-Za-z0-9_.-]+', s) for s in p.parts):
        raise ValueError('RELATIVE_SAFE_ASSET_PATH_REQUIRED')
    return p.as_posix()


def freeze_files(freeze):
    values = freeze['files']
    return values if type(values) is list else [dict(path=name, **pin) for name,pin in values.items()]


def esc(value):
    return html.escape(str(value), quote=True)


def case_rows(cases, asset_base):
    texts = {name:(label,question) for name,label,question in CASES}
    rows = []
    for case in cases:
        case_id = case['case_id']; label,question = texts[case_id]
        off = case['actual_disabled_setting']
        verdict = '预期物理失败 · 原样保留' if off else '条件夹具校准通过'
        badge = 'negative' if off else 'positive'
        extra = '<small class="v03-uncertain">创建顺序机制：INCONCLUSIVE</small>' if 'c3_actor' in case_id else ''
        if off: extra = '<small>49/49 点的 mg 与速度差分支撑检查均失败</small>'
        report_url=f'{asset_base}/actual_audits/{case_id}/REPORT.json'
        series_url=f'{asset_base}/actual_audits/{case_id}/AUDITED_SERIES.json'
        lo,hi=case['window']
        rows.append(f'''<tr data-case="{esc(case_id)}" data-status="{esc(case['status'])}"><td data-label="案例"><strong>{label}</strong><small>{question}</small></td><td data-label="接触报告">{'OFF' if off else 'ON'}<small>实读 disabled = {str(off).lower()}</small></td><td data-label="受控步 / 固定窗口">{case['controlled_steps']} 步<small>tick {lo}–{hi} · 49 点 · 1 epoch</small></td><td data-label="独立审计"><span class="v03-pill {badge}">{verdict}</span>{extra}</td><td data-label="证据"><a href="{esc(report_url)}">独立报告 ↗</a><a href="{esc(series_url)}">全部 49 点 ↗</a></td></tr>''')
    return '\n'.join(rows)


def section(closure, asset_base, raw_available):
    cases = closure['cases']; by_id = {c['case_id']:c for c in cases}
    on = by_id['cal_force_c1_stack_v03']; off = by_id['cal_force_c1_stack_processing_off_v03']
    ratio = closure['c4_to_c1_mean_support_ratio']
    raw = f'<a href="{esc(asset_base)}/raw/native_raw_v03_complete_inputs.zip">六案完整原始记录 ZIP ↗</a>' if raw_available else '<span class="v03-pending">原始记录公开包待复制；审计报告与全部序列已提供。</span>'
    return f'''{START}
<section id="calibration-v03" data-evidence-status="FIVE_POSITIVE_CONDITIONAL_FIXTURES_PASS_NEGATIVE_FAILURE_RETAINED" aria-labelledby="v03-title">
<div class="v03-heading"><div><p class="eyebrow">LATEST / V03 · ACTUAL NATIVE EVIDENCE</p><h2 id="v03-title">接触报告开关对照完成，<br>五项夹具条件校准通过。</h2></div><span class="v03-pill positive">6 案已关闭 · 每案一次</span></div>
<p class="v03-lead">v02 的零接触报告问题有了同源反事实对照：关闭接触处理时，稳定堆叠仍报告零支撑力；开启后，固定窗口恢复与已知模拟重力一致的世界支撑力。各案阈值、几何、dt 和计分窗口沿用封存协议。</p>
<div class="v03-metrics"><div><strong>5 / 5</strong><span>正向条件夹具通过</span></div><div><strong>49 / 49</strong><span>OFF 对照的支撑检查失败，完整保留</span></div><div><strong>≈ 2×</strong><span>质量倍增后的平均支撑力比<br>实测 {ratio:.9f}×</span></div><div><strong>1 epoch</strong><span>每案一次原生执行、一次冻结 reader</span></div></div>
<div class="v03-comparison"><article><span class="v03-pill negative">OFF · 预声明负对照</span><h3>物体被支撑，接触报告却为零</h3><p>同一个 C1 夹具，实际关闭设置在全部 {off['all_controlled_setting_readbacks']} 个受控步骤读回为 true。平均接触对力为 <b>0 N</b>，全部 49 点支撑检查均失败；这是预期负对照，不能计为正向校准。</p></article><article><span class="v03-pill positive">ON · 同源 C1</span><h3>实际支撑力回到模拟 mg</h3><p>实际关闭设置在全部 {on['all_controlled_setting_readbacks']} 步读回为 false。平均世界 z 支撑力 <b>{on['mean_pair_world_N'][2]:.9f} N</b>，最大支撑残差 <b>{on['max_support_error_N']:.3g} N</b>。有符号 contact scalar 保留负值，未取绝对值或删除。</p></article></div>
<div class="v03-table-container"><table id="v03-case-table"><caption>六案的实际执行与独立测量判定 · 固定协议、完整窗口</caption><thead><tr><th scope="col">案例与问题</th><th scope="col">实际接触报告</th><th scope="col">受控步 / 窗口</th><th scope="col">独立审计</th><th scope="col">实际证据</th></tr></thead><tbody>{case_rows(cases,asset_base)}</tbody></table></div>
<figure id="force-v03-figure"><div class="v03-figure-head"><div><p class="eyebrow">ACTUAL / ALL 49 · UNSMOOTHED</p><h3>六案完整固定窗口，不挑选曲线</h3></div><a href="{esc(asset_base)}/figures/signed_force_calibration.pdf">矢量 PDF ↗</a></div><a href="{esc(asset_base)}/figures/signed_force_calibration.svg" aria-label="打开实际六案矢量图"><img src="{esc(asset_base)}/figures/signed_force_calibration.svg" alt="v03六案实际全部49点：自由落体加速度、开启支撑力、旋转世界力、创建顺序对照、质量倍增及关闭处理的零力负对照；负对照失败保留。" width="1400" loading="eager" decoding="async"></a><figcaption>每个点来自已 hash 绑定的独立审计序列。每案是一个原生 epoch，49 个窗口点不是 49 次独立试验；无平滑、无窗口搜索、无额外重跑。<a href="{esc(asset_base)}/figures/FIGURE_RECEIPT.json">图与输入摘要 ↗</a></figcaption></figure>
<div class="v03-limits"><h3>这些结果证明到哪一步</h3><p>C3 的世界力一致性检查通过，实际 actor 顺序代理发生变化；完整 backend shape 顺序仍不可观测，因此创建顺序机制为 <b>INCONCLUSIVE</b>。这些是模拟夹具的条件测量证据，尚未证明硬件 SI、全机器人承重/卸载/扭矩或完整隐藏约束。</p><p>六案正常退出支持当前受控生命周期；缺少 AFTER_APP_CLOSE 标记，Python 关闭函数实际返回仍为 <b>UNKNOWN</b>。主方法 <b>M vs B3：UNTESTED</b>；训练 GPU 时间 <b>0</b>，合格 S/F/R <b>0</b>，真实化学终点 <b>0</b>。</p></div>
<div class="v03-accounting"><p>本批次 <b>{closure['actual_v03_epochs']} 个新 epoch / {closure['actual_controlled_steps']:,} 个受控步骤</b>；此前校准实际 3 案仍保留，校准家族累计 <b>{closure['calibration_family_actual_epochs']}</b>。关闭诊断 1 案与旧 M 家族另计。v01 剩余四案、v02 剩余三案仍未执行；本页发布不增加实验授权。</p><p>下面的 v01 / diagnostic / v02 历史、失败表与旧曲线继续保留。</p></div>
<div class="v03-downloads"><a href="{esc(asset_base)}/root_execution/ROOT_BATCH_V03_ACTUAL_CLOSURE.json">根执行封存结论 ↗</a><a href="{esc(asset_base)}/collector/force_fixture_v03_source.zip">采集器封存包 ↗</a><a href="{esc(asset_base)}/independent_reader/force_fixture_v03_independent_reader_source.zip">独立 reader 封存包 ↗</a><a href="{esc(asset_base)}/DATA/source_inventory.json">全部公开材料 SHA ↗</a>{raw}</div>
</section>
{END}'''


CSS = '''#calibration-v03{border:1px solid #bad7c6;border-top:5px solid #226b45;border-radius:20px;background:#f6fbf7;padding:clamp(20px,4vw,42px);margin:34px 0 48px;overflow-wrap:anywhere;box-sizing:border-box}#calibration-v03 *{box-sizing:border-box}#calibration-v03 .v03-heading{display:flex;justify-content:space-between;align-items:flex-start;gap:22px}#calibration-v03 h2{font-size:clamp(25px,3.4vw,39px);line-height:1.28;margin:10px 0 20px}#calibration-v03 .v03-lead{max-width:880px;line-height:1.9;color:#41574b}#calibration-v03 .v03-pill{display:inline-block;border-radius:999px;padding:7px 12px;font-size:12px;line-height:1.4;font-weight:700}#calibration-v03 .positive{background:#daefe1;color:#185333}#calibration-v03 .negative{background:#f8e5db;color:#8b391d}#calibration-v03 .v03-metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:28px 0}#calibration-v03 .v03-metrics>div{padding:20px 16px;border:1px solid #d5e5db;background:white;border-radius:12px}#calibration-v03 .v03-metrics strong{display:block;font-size:clamp(19px,2.2vw,28px);letter-spacing:-.7px;color:#20583a;line-height:1.3}#calibration-v03 .v03-metrics span{display:block;margin-top:8px;font-size:12px;line-height:1.6;color:#627368}#calibration-v03 .v03-comparison{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin:24px 0}#calibration-v03 .v03-comparison article{border:1px solid #d7e3db;border-radius:14px;padding:24px;background:white}#calibration-v03 h3{font-size:20px;line-height:1.45;margin:14px 0 10px}#calibration-v03 p{line-height:1.8}#calibration-v03 table{border-collapse:collapse;width:100%;table-layout:fixed;font-size:13px;background:white}#calibration-v03 caption{text-align:left;font-size:13px;font-weight:600;padding:10px 0 16px;color:#53685b}#calibration-v03 th{font-weight:600;color:#506558;background:#e9f3ec}#calibration-v03 th,#calibration-v03 td{padding:16px 12px;text-align:left;vertical-align:top;border-bottom:1px solid #dbe7df}#calibration-v03 th:first-child{width:26%}#calibration-v03 th:nth-child(2){width:16%}#calibration-v03 th:nth-child(3){width:20%}#calibration-v03 th:nth-child(4){width:24%}#calibration-v03 th:last-child{width:14%}#calibration-v03 td{min-width:0}#calibration-v03 td small{display:block;color:#64766b;line-height:1.65;font-size:11px;margin-top:7px}#calibration-v03 td a{display:block;line-height:1.8;font-size:12px}#calibration-v03 td .v03-uncertain{color:#96651f;font-weight:700}#calibration-v03 #force-v03-figure{margin:28px 0;background:white;border:1px solid #d8e6dc;border-radius:14px;padding:clamp(10px,2vw,24px);min-width:0}#calibration-v03 .v03-figure-head{display:flex;justify-content:space-between;align-items:center;gap:14px}#calibration-v03 #force-v03-figure img{display:block;width:100%;max-width:100%;height:auto;margin-top:15px}#calibration-v03 figcaption{font-size:12px;line-height:1.8;color:#5b6d61;margin-top:14px}#calibration-v03 figcaption a{margin-left:10px}#calibration-v03 .v03-limits{border-left:3px solid #b49054;padding:4px 18px;background:#fffdf6;margin-top:24px}#calibration-v03 .v03-limits p{font-size:13px;color:#596355}#calibration-v03 .v03-accounting{font-size:12px;color:#65756b;padding:12px 0}#calibration-v03 .v03-downloads{display:flex;flex-wrap:wrap;gap:10px 24px;border-top:1px solid #d4e4d9;padding-top:18px;font-size:12px;line-height:1.8}#calibration-v03 .v03-pending{color:#846239}@media(max-width:850px){#calibration-v03 .v03-metrics{grid-template-columns:repeat(2,minmax(0,1fr))}#calibration-v03 .v03-heading{display:block}#calibration-v03 table{font-size:12px}}@media(max-width:650px){#calibration-v03 .v03-comparison{grid-template-columns:1fr}#calibration-v03 .v03-table-container{overflow:visible}#calibration-v03 table,#calibration-v03 tbody,#calibration-v03 tr,#calibration-v03 td{display:block;width:100%}#calibration-v03 thead{display:none}#calibration-v03 tr{border:1px solid #d4e4d9;border-radius:10px;margin-bottom:14px;overflow:hidden;background:white}#calibration-v03 td{border:none;padding:8px 14px;font-size:13px}#calibration-v03 td:first-child{padding-top:15px}#calibration-v03 td:last-child{padding-bottom:15px}#calibration-v03 td::before{content:attr(data-label);display:block;font-size:10px;font-weight:700;color:#718378;margin-bottom:5px}#calibration-v03 .v03-figure-head{display:block}#calibration-v03 .v03-figure-head>a{font-size:12px}#calibration-v03 .v03-metrics>div{padding:14px 12px}#calibration-v03 .v03-metrics strong{font-size:20px}}
'''


def build(args):
    asset_base=relative(args.asset_base)
    site=Path(args.site).resolve();site.mkdir(parents=True,exist_ok=True)
    page=site/'calibration.html'
    if not page.exists():
        if not args.base_page: raise ValueError('EXISTING_CALIBRATION_PAGE_OR_BASE_PAGE_REQUIRED')
        shutil.copyfile(args.base_page,page)
    old_page=page.read_text();old_page_sha=sha(page)
    marker='<section id="calibration-evidence">'
    if old_page.count(marker)!=1: raise ValueError('ONE_EXISTING_HISTORY_SECTION_REQUIRED')
    closure_path=INCREMENT/'root_execution/ROOT_BATCH_V03_ACTUAL_CLOSURE.json'
    closure=bound_json(closure_path,CLOSURE_SHA)
    if closure['execution_state']!='CLOSED_ALL6_DISTINCT_CASES_ONCE' or [c['case_id'] for c in closure['cases']]!=[c[0] for c in CASES]:
        raise ValueError('ACTUAL_SIX_PREDECLARED_CASES_REQUIRED')
    if closure['qualified_S_F_R']!=0 or closure['main_M_B3']!='UNTESTED' or closure['real_hardware_chemical_endpoints']!=0:
        raise ValueError('METHOD_LIMITS_CHANGED_REVIEW_REQUIRED')
    inventory=[]
    def copy_file(source,destination,expected=None):
        source=Path(source).resolve();destination=relative(destination)
        actual=sha(source)
        if expected is not None and actual!=expected: raise ValueError(f'COPY_INPUT_SHA_MISMATCH: {source}')
        target=site/asset_base/destination;target.parent.mkdir(parents=True,exist_ok=True)
        if target.is_symlink(): raise ValueError('SYMLINK_DESTINATION_REJECTED')
        shutil.copyfile(source,target)
        if sha(target)!=actual: raise ValueError('COPY_READBACK_SHA_MISMATCH')
        inventory.append({'source':str(source),'destination':f'{asset_base}/{destination}','sha256':actual,'bytes':target.stat().st_size})
    for sub,freeze_name,pin,archive_name in (
        ('collector','SOURCE_FREEZE.json',COLLECTOR_FREEZE_SHA,'force_fixture_v03_source.zip'),
        ('independent_reader','PROSPECTIVE_READER_FREEZE.json',READER_FREEZE_SHA,'force_fixture_v03_independent_reader_source.zip')):
        source_dir=INCREMENT/sub; freeze=bound_json(source_dir/freeze_name,pin)
        for item in freeze_files(freeze):
            name=relative(item['path']);copy_file(source_dir/name,f'{sub}/{name}',item['sha256'])
        copy_file(source_dir/freeze_name,f'{sub}/{freeze_name}',pin)
        final=json.loads((source_dir/'FINAL_RECEIPT.json').read_text())
        archive_sha=final.get('archive_sha256',final.get('reader_archive_sha256'))
        copy_file(source_dir/archive_name,f'{sub}/{archive_name}',archive_sha)
        copy_file(source_dir/'FINAL_RECEIPT.json',f'{sub}/FINAL_RECEIPT.json')
    copy_file(INCREMENT/'independent_reader/SOURCE_REVIEW.json','independent_reader/SOURCE_REVIEW.json',READER_REVIEW_SHA)
    copy_file(closure_path,'root_execution/ROOT_BATCH_V03_ACTUAL_CLOSURE.json',CLOSURE_SHA)
    copy_file(Path(__file__),'publication/build_v03_supplement.py')
    for name in ('ROOT_PROSPECTIVE_BATCH_SELECTION.json',):
        copy_file(INCREMENT/name,name)
    for name in ('ROOT_SOURCE_READER_FULL_READBACK.json','ROOT_SOURCE_PROTOCOL_READBACK.json','ROOT_READER_PIN_EXPECTATIONS.json','ROOT_PROSPECTIVE_ADAPTER_CORRECTION.json','ROOT_PROSPECTIVE_CLEANUP_MARKER_COORDINATION.json'):
        path=INCREMENT/'root_execution'/name
        if path.exists(): copy_file(path,f'root_execution/{name}')
    for case in closure['cases']:
        cid=case['case_id']
        report=bound_json(case['report']['path'],case['report']['sha256'])
        series=bound_json(case['series']['path'],case['series']['sha256'])
        if report['case_id']!=cid or report['status']!=case['status'] or report['series_sha256']!=case['series']['sha256'] or report['S_F_R_admitted']!=0:
            raise ValueError('REPORT_CLOSURE_STATUS_OR_SERIES_MISMATCH')
        if report['samples']!=49 or report['fixed_window_inclusive']!=case['window'] or report['contact_processing_readback']['actual_disabled_value'] is not case['actual_disabled_setting']:
            raise ValueError('REPORT_ACTUAL_WINDOW_SETTING_MISMATCH')
        if len(series['rows'])!=49 or [row['tick'] for row in series['rows']]!=list(range(case['window'][0],case['window'][1]+1)):
            raise ValueError('COMPLETE_ACTUAL49_REQUIRED')
        for key,name in (('report','REPORT.json'),('series','AUDITED_SERIES.json')):
            copy_file(case[key]['path'],f'actual_audits/{cid}/{name}',case[key]['sha256'])
        copy_file(case['terminal']['path'],f'root_execution/{cid}/WORKER_TERMINAL.json',case['terminal']['sha256'])
        request=INCREMENT/'root_execution'/cid/'ROOT_TERMINAL_AUDIT_REQUEST.json'
        copy_file(request,f'root_execution/{cid}/ROOT_TERMINAL_AUDIT_REQUEST.json',report['request_sha256'])
        admission=report['input_files']['ROOT_ADMISSION.json']
        copy_file(admission['path'],f'root_execution/{cid}/ROOT_ADMISSION.json',admission['sha256'])
    figure_receipt=json.loads((HERE/'figures/FIGURE_RECEIPT.json').read_text())
    if figure_receipt['fixed_window_samples_per_case']!=49 or figure_receipt['smoothing'] or figure_receipt['window_search']:
        raise ValueError('ACTUAL_FIXED49_UNSMOOTHED_FIGURE_REQUIRED')
    for case in closure['cases']:
        figure_input=figure_receipt['input_audits'][case['case_id']]
        if figure_input['report_sha256']!=case['report']['sha256'] or figure_input['series_sha256']!=case['series']['sha256']:
            raise ValueError('FIGURE_INPUT_SHA_MISMATCH')
    for name,pin in figure_receipt['outputs'].items():
        copy_file(HERE/'figures'/relative(name),f'figures/{relative(name)}',pin['sha256'])
    copy_file(HERE/'figures/FIGURE_RECEIPT.json','figures/FIGURE_RECEIPT.json')
    raw_available=False
    if args.raw_zip:
        if not args.raw_sha256 or not re.fullmatch(r'[0-9a-f]{64}',args.raw_sha256): raise ValueError('EXTERNAL_RAW_ARCHIVE_SHA_REQUIRED')
        copy_file(args.raw_zip,'raw/native_raw_v03_complete_inputs.zip',args.raw_sha256)
        raw_receipt_path=Path(args.raw_receipt) if args.raw_receipt else HERE/'NATIVE_RAW_V03_COMPLETE_INPUTS_RECEIPT.json'
        raw_receipt=json.loads(raw_receipt_path.read_text())
        if raw_receipt['archive_sha256']!=args.raw_sha256 or raw_receipt['actualcases']!=6 or raw_receipt['all12_inputs_byteexact'] is not True or raw_receipt['CRC']!='PASS':
            raise ValueError('SIX_CASE_COMPLETE_RAW_RECEIPT_REQUIRED')
        copy_file(raw_receipt_path,'raw/NATIVE_RAW_V03_COMPLETE_INPUTS_RECEIPT.json')
        raw_available=True
    elif not args.allow_pending_raw:
        raise ValueError('FULL_RAW_ZIP_REQUIRED_OR_EXPLICIT_PREVIEW_ONLY_PENDING_FLAG')
    fragment=section(closure,asset_base,raw_available)
    current=old_page
    if START in current or END in current:
        if current.count(START)!=1 or current.count(END)!=1: raise ValueError('EXACT_SUPPLEMENT_BOUNDARIES_REQUIRED')
        lo=current.index(START);hi=current.index(END)+len(END)
        if current[hi:hi+1]=='\n': hi += 1
        current=current[:lo]+current[hi:]
    current=current.replace(marker,fragment+'\n'+marker,1)
    css_link=f'<link data-v03-supplement="true" rel="stylesheet" href="{esc(asset_base)}/calibration-v03.css">'
    current=re.sub(r'<link data-v03-supplement="true"[^>]*>', '', current)
    if '</head>' not in current: raise ValueError('HTML_HEAD_REQUIRED')
    current=current.replace('</head>',css_link+'</head>',1)
    # Old history, old table, old figure, base JS and data sources are not rewritten.
    page.write_text(current)
    generated={
        'calibration-v03.css':CSS,
        'SECTION.html':fragment,
        'DATA/status.json':json.dumps({'schema':'PaperBPublicV03CalibrationStatus/1','source_closure_sha256':CLOSURE_SHA,'source_closure':f'{asset_base}/root_execution/ROOT_BATCH_V03_ACTUAL_CLOSURE.json','status':closure['status'],'cases':[{k:v for k,v in case.items() if k not in ('report','series','terminal')} for case in closure['cases']],'fixed_window_samples':49,'native_epochs_per_case':1,'c4_to_c1_mean_support_ratio':closure['c4_to_c1_mean_support_ratio'],'full_raw_zip_available':raw_available,'qualified_S_F_R':0,'main_M_B3':'UNTESTED','real_hardware_chemical_endpoints':0},ensure_ascii=False,indent=2)+'\n'}
    for name,data in generated.items():
        dest=site/asset_base/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(data)
        inventory.append({'source':'BUILDER_GENERATED_FROM_PINNED_ACTUALS','destination':f'{asset_base}/{name}','sha256':sha(dest),'bytes':dest.stat().st_size})
    inv={'schema':'PaperBV03PublicationCopyInventory/1','root_closure_sha256':CLOSURE_SHA,'raw_decode_or_physics_rescore':False,'files':inventory,'native_GPU_model_calls':0}
    inv_path=site/asset_base/'DATA/source_inventory.json';inv_path.write_text(json.dumps(inv,ensure_ascii=False,indent=2)+'\n')
    receipt={'schema':'PaperBV03PublicationBuildReceipt/1','status':'BUILT_ACTUAL_SIX_CASE_SECTION','site':str(site),'asset_base':asset_base,'root_closure_sha256':CLOSURE_SHA,'builder_sha256':sha(Path(__file__)),'base_page_before_sha256':old_page_sha,'page_after_sha256':sha(page),'inventory_sha256':sha(inv_path),'copy_count':len(inventory),'fixed49_series_cases':6,'native_epochs_per_case':1,'raw_complete_zip_copied':raw_available,'history_injection_point':'BEFORE_calibration-evidence','base_JS_or_history_edits':False,'native_GPU_model_calls':0,'publication_or_git_calls':0}
    (site/asset_base/'BUILD_RECEIPT.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(receipt,ensure_ascii=False,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--site',required=True,help='Existing site checkout/output; author uses _preview only')
    p.add_argument('--base-page',help='Existing calibration.html to copy only if destination absent')
    p.add_argument('--asset-base',default=f'research_increments/{NAME}')
    p.add_argument('--raw-zip');p.add_argument('--raw-sha256');p.add_argument('--raw-receipt')
    p.add_argument('--allow-pending-raw',action='store_true',help='Preview only; no missing RAW download link')
    build(p.parse_args())
