(() => {
  'use strict';
  const $=id=>document.getElementById(id);
  const metricNames={allowed_cost:'Allowed cost',member_months:'Member-months',pmpm:'PMPM',members_with_episode_pct:'Members with an episode',admissions_per_1000:'Admissions per 1,000',risk_score:'Risk score'};
  const statusNames={definition_mismatch:'Definition changed',duplicate_source:'Duplicate source key',duplicate_target:'Duplicate target key',missing_target:'Missing target row',unexpected_target:'Unexpected target row',invalid_value:'Invalid value',value_mismatch:'Outside tolerance',within_tolerance:'Within tolerance',exact_match:'Exact match',missing_policy:'Missing metric policy',unit_policy_mismatch:'Unit policy mismatch',incomplete_definition:'Incomplete definition'};
  const explanations={definition_mismatch:'The documented definitions differ. Matching values would not be sufficient to pass this comparison.',duplicate_source:'More than one source row has this business key. No single source value is selected.',duplicate_target:'More than one target row has this business key. No single target value is selected.',missing_target:'This source business key has no target row. It remains visible because the audit uses the union of keys.',unexpected_target:'This target business key is not present in the source snapshot. Confirm whether the scope change was intended.',invalid_value:'At least one value is blank, nonnumeric, nonfinite, negative, or violates the integer policy. It cannot be compared numerically.',value_mismatch:'The definitions agree, but the absolute difference exceeds the declared metric tolerance.',within_tolerance:'The definitions agree. The nonzero difference is within the inclusive absolute tolerance.',exact_match:'The documented definitions and numeric values agree.',missing_policy:'This metric has no declared comparison policy.',unit_policy_mismatch:'At least one unit differs from the declared metric policy.',incomplete_definition:'At least one required definition field is missing.'};
  let data,visible=[];
  const text=(tag,value,className)=>{const el=document.createElement(tag);el.textContent=value;if(className)el.className=className;return el;};
  const valueLabel=(row,side)=>row[side+'_count']===0?'Missing':row[side+'_count']>1?'Duplicate':row[side+'_value']==null?'Blank':row[side+'_value'];
  function auditRow(row){
    const item=document.createElement('details');item.className='audit-row';
    const summary=document.createElement('summary');
    const name=document.createElement('span');name.append(text('span',metricNames[row.metric]||row.metric,'audit-name'),text('span',`${row.period} · ${row.plan} · ${row.cohort}`,'audit-key'));
    const values=document.createElement('span');values.className='audit-values';values.append(text('small','SOURCE → TARGET'),text('span',`${valueLabel(row,'source')} → ${valueLabel(row,'target')}`));
    const status=text('span',statusNames[row.status]||row.status,'audit-status'+(row.needs_review?'':' pass'));
    summary.append(name,values,status);item.append(summary);
    const body=document.createElement('div');body.className='audit-body';body.append(text('p',explanations[row.status]||'Review the documented comparison.'));
    const definitions=document.createElement('dl');
    const add=(label,value)=>{definitions.append(text('dt',label),text('dd',value==null?'Not comparable / not available':String(value)));};
    add('Source / target rows',`${row.source_count} / ${row.target_count}`);
    add('Source / target unit',`${row.source_unit??'—'} / ${row.target_unit??'—'}`);
    add('Absolute tolerance',row.absolute_tolerance);
    add('Numerical difference',row.delta);
    for(const change of row.definition_changes)add(change.field.replaceAll('_',' '),`${change.source} → ${change.target}`);
    if(!row.definition_changes.length&&row.source_count===1&&row.target_count===1){add('Time basis',row.source_time_basis);add('Denominator',row.source_denominator);add('Filters',row.source_filters);}
    if(row.reasons.length)add('Review reasons',row.reasons.map(r=>statusNames[r]||r).join('; '));
    body.append(definitions);item.append(body);return item;
  }
  function render(){
    const status=$('status').value,metric=$('metric').value;
    visible=data.results.filter(r=>(status==='all'||(status==='review'?r.needs_review:!r.needs_review))&&(metric==='all'||r.metric===metric));
    $('scope').textContent=`${visible.length} of ${data.results.length} keys shown · ${$('status').selectedOptions[0].textContent} · ${metric==='all'?'All metrics':metricNames[metric]} · Synthetic snapshots`;
    $('ledger').replaceChildren(...(visible.length?visible.map(auditRow):[text('p','No comparisons match these filters.','empty')]));
  }
  function download(){
    const fields=['data_kind','metric','period','plan','cohort','source_count','target_count','source_value','target_value','source_unit','target_unit','status','delta','absolute_tolerance','reasons'];
    const quote=value=>`"${String(value??'').replaceAll('"','""')}"`;
    const lines=[fields.map(quote).join(','),...visible.map(row=>fields.map(field=>quote(field==='data_kind'?'synthetic':field==='reasons'?row.reasons.join('; '):row[field])).join(','))];
    const url=URL.createObjectURL(new Blob([lines.join('\r\n')+'\r\n'],{type:'text/csv;charset=utf-8'}));
    const a=document.createElement('a');a.href=url;a.download='synthetic-migration-audit-filtered.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  fetch('data.json').then(response=>{if(!response.ok)throw new Error('Data unavailable');return response.json();}).then(payload=>{
    if(payload.data_kind!=='synthetic'||!Array.isArray(payload.results))throw new Error('Unexpected data');data=payload;
    $('review-count').textContent=data.summary.review;$('key-count').textContent=data.summary.compared_keys;$('pass-count').textContent=data.summary.passed;$('rounding-count').textContent=data.summary.status_counts.within_tolerance||0;
    const checks=data.summary.checks;$('quality-title').textContent=`${Object.values(checks).filter(Boolean).length} of ${Object.keys(checks).length} reconciliation checks passed`;
    $('quality-note').textContent=`${data.summary.source_rows} source rows and ${data.summary.target_rows} target rows produce ${data.summary.compared_keys} distinct business keys.`;
    $('status').addEventListener('change',render);$('metric').addEventListener('change',render);$('reset').addEventListener('click',()=>{$('status').value='review';$('metric').value='all';render();});$('download').addEventListener('click',download);$('explorer').hidden=false;render();
  }).catch(error=>{$('error').hidden=false;$('explorer').hidden=true;console.error('Migration demonstration unavailable',error);});
})();
