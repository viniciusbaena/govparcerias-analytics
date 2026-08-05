const APP_VERSION='v3.16.0-alpha';
const S={data:null,contract:null,portfolio:null,contracts:[],proposals:[],integrated:{},discretionary:{},view:'inicio',homeQuery:'',dossierQuery:'',theme:localStorage.getItem('gpa:theme')||'dark',selectedSection:'identificacao',selectedMunicipality:null,selectedOfficialProposal:null,selectedOfficialContract:null,municipalityQuery:'',municipalityPage:1,instrumentContractPage:1,pageSize:18,instrumentPageSize:20};
const $=q=>document.querySelector(q); const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
document.addEventListener('click',event=>{
  const button=event.target.closest('[data-action]');
  if(!button||button.disabled)return;
  const action=button.dataset.action;
  const value=button.dataset.value;
  const actions={
    'show':()=>show(value),
    'toggle-theme':toggleTheme,
    'open-palette':openPalette,
    'export-current':exportCurrent,
    'close-chat':closeChat,
    'assistant-query':assistantQuery,
    'close-palette':()=>{closePalette();show(value)},
    'municipality-search':applyMunicipalitySearch,
    'municipality-page':()=>changeMunicipalityPage(Number(value)),
    'instrument-contract-page':()=>{S.instrumentContractPage=Math.max(1,S.instrumentContractPage+Number(value));instrumentos()},
    'open-municipality':()=>openMunicipality(value),
    'municipality-tab':()=>showMunicipalityTab(value),
    'open-contract':()=>openContractResult(Number(value)),
    'open-transfer-contract':()=>openTransferContract(value),
    'open-proposal':()=>openProposalResult(Number(value)),
    'select-section':()=>selectSection(value),
    'select-dossier-contract':()=>{S.selectedOfficialContract=(S.contracts||[])[Number(value)];S.selectedSection='identificacao';dossie()},
    'dossier-search':applyDossierSearch,
    'open-chat':openChat,
  };
  if(actions[action]){
    event.preventDefault();
    actions[action]()
  }
});
document.addEventListener('keydown',event=>{
  if(event.key==='Enter'&&event.target?.id==='chatInput'){
    assistantQuery();
    return
  }
  if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==='k'){
    event.preventDefault();
    openPalette()
  }
  if(event.key==='Escape'){
    closePalette();
    closeChat()
  }
});
async function boot(){
  const safeJson=async(url,fallback)=>{
    try{
      const r=await fetch(url+'?v='+Date.now(),{cache:'no-store'});
      if(!r.ok)throw new Error(url+' HTTP '+r.status);
      return await r.json()
    }catch(err){
      console.error('Falha ao carregar',url,err);
      return fallback
    }
  };
  [S.data,S.contract,S.portfolio,S.contracts,S.proposals,S.integrated]=await Promise.all([
    safeJson('data/demo.json',{}),
    safeJson('data/dossier-contract.json',{sections:[]}),
    safeJson('data/municipalities.json',{manifest:{record_count:0},municipalities:[]}),
    safeJson('data/contracts.json',[]),
    safeJson('data/proposals.json',[]),
    safeJson('data/integrated.json',{counts:{},financial:{records:{}},timeline:[],integrity:{rules:[]}})
  ]);
  const fragments=S.integrated?.transferegov_discretionary?.records||{};
  const entries=Object.entries(fragments).filter(([,meta])=>meta?.path);
  if(entries.length){
    const loaded=await Promise.all(entries.map(async([name,meta])=>[name,await safeJson(meta.path,[])]));
    S.integrated.transferegov_discretionary_records=Object.fromEntries(loaded);
    S.discretionary=S.integrated.transferegov_discretionary_records;
  }
  if(!Array.isArray(S.contracts))S.contracts=S.contracts.items||S.contracts.contracts||S.contracts.data||[];
  if(!Array.isArray(S.proposals))S.proposals=S.proposals.items||S.proposals.proposals||S.proposals.data||[];
  document.documentElement.dataset.theme=S.theme;
  renderShell();
  document.querySelector('.badge')?.replaceChildren(document.createTextNode(APP_VERSION));
  show('inicio')
}
const nav=[['inicio','Visão integrada'],['municipios','Municípios'],['territorial','Gestão territorial'],['instrumentos','Contratos e propostas'],['dossie','Dossiê por contrato'],['financeiro','Inteligência financeira'],['engenharia','Obras e engenharia'],['documentos','Centro de documentos'],['timeline','Timeline integrada'],['riscos','Risco e conformidade'],['copiloto','Copiloto']];
function renderShell(){$('#app').innerHTML=`<div class="layout"><aside class="sidebar"><div class="brand"><div class="logo">GP</div><div><strong>GovParcerias</strong><small>Intelligence</small></div></div><nav>${nav.map(([id,t])=>`<button data-view="${id}" data-action="show" data-value="${id}">${t}</button>`).join('')}</nav><div class="policy">Integridade official-only<br><small>Carteira administrativa separada da base pública oficial.</small></div></aside><main><header class="topbar"><div><strong>Operação por contrato · gestão por território</strong><small> Uma base, duas jornadas complementares</small></div><div><button id="cmd" data-action="open-palette">Ctrl K</button><button data-action="export-current" title="Exportar dados oficiais da página">Exportar CSV</button><button id="theme" data-action="toggle-theme">${S.theme==='dark'?'Claro':'Escuro'}</button><span class="badge">v3.4.0-alpha</span></div></header><section id="content"></section><footer>121 municípios · ${(S.proposals||[]).length} propostas Transferegov · ${(S.contracts||[]).length} contratos PNCP · official-only</footer></main></div><aside id="chat" class="chat"><header><div><strong>Copiloto verificável</strong><small>Território, município e contrato</small></div><button data-action="close-chat" aria-label="Fechar copiloto">×</button></header><div class="chat-body" id="chatBody"><div class="notice"><strong>Política ativa.</strong> A carteira identifica o universo de trabalho. Respostas sobre contratos, propostas, valores, obras e documentos exigem evidência pública oficial.</div></div><div class="chat-input"><input id="chatInput" placeholder="Pergunte por município, proposta ou contrato"><button data-action="assistant-query">Enviar</button></div></aside><div id="palette" class="palette"><div class="palette-box"><input id="paletteInput" placeholder="Digite uma página ou comando"><div>${nav.map(([id,t])=>`<button data-action="close-palette" data-value="${id}">${t}</button>`).join('')}</div></div></div>`}
function toggleTheme(){S.theme=S.theme==='dark'?'light':'dark';document.documentElement.dataset.theme=S.theme;localStorage.setItem('gpa:theme',S.theme);renderShell();document.querySelector('.badge')?.replaceChildren(document.createTextNode(APP_VERSION));show(S.view)}
function show(v){S.view=v;document.querySelectorAll('[data-view]').forEach(b=>b.classList.toggle('active',b.dataset.view===v));({inicio,municipios,territorial,instrumentos,dossie,financeiro,engenharia,documentos,timeline,riscos,copiloto}[v]||inicio)()}
const head=(t,p,a='')=>`<div class="hero"><div><h1>${t}</h1><p>${p}</p></div>${a}</div>`;
const empty=(title='Nenhum dado oficial sincronizado',detail='A estrutura está pronta e não será preenchida por estimativas ou demonstrações fictícias.')=>`<div class="empty"><div class="empty-icon">✓</div><h2>${title}</h2><p>${detail}</p></div>`;
const card=(label,value,detail='')=>`<article class="metric"><span>${label}</span><strong>${value}</strong><small>${detail}</small></article>`;
function inicio(){
  const m=S.portfolio?.manifest||{};
  const totalContracts=Array.isArray(S.contracts)?S.contracts.length:0;
  const totalProposals=Array.isArray(S.proposals)?S.proposals.length:0;
  $('#content').innerHTML=
    head('Consulta unificada','Comece pelo número do contrato/convênio ou pelo nome do município. CNPJ e IBGE são filtros secundários; propostas ficam disponíveis como consulta complementar.')
    +`<div class="home-search-grid">
      <article class="home-search-card">
        <span class="eyebrow">Busca integrada</span>
        <h2>Consultar propostas, contratos, obras, documentos e municípios</h2>
        <p>A pesquisa combina a carteira dos 121 municípios com registros oficiais do Transferegov, PNCP e ObrasGov.</p>
        <div class="home-search">
          <input id="unifiedHomeSearch" value="${esc(S.homeQuery||'')}" placeholder="Ex.: contrato 123, Altamira, CNPJ, IBGE ou proposta">
          <button class="primary" id="unifiedSearchButton">Consultar</button>
        </div>
        <small>Resultados são exibidos somente quando existem nas bases oficiais sincronizadas.</small>
      </article>
      <article class="home-search-card ai-home-card">
        <span class="eyebrow">GovParcerias AI</span>
        <h2>Converse com a inteligência da plataforma</h2>
        <p>Use linguagem natural para consultar propostas, contratos e municípios disponíveis na base.</p>
        <div id="aiConversation" class="ai-conversation">
          <div class="notice"><strong>Exemplos:</strong><br>“Mostre os contratos de Altamira”<br>“Existe contrato número 100?”<br>“Quais registros mencionam PNAE?”</div>
        </div>
        <div class="home-search">
          <input id="aiHomeInput" placeholder="Faça uma pergunta sobre a base sincronizada">
          <button class="primary" id="aiHomeButton">Perguntar</button>
        </div>
        <small>As respostas são restritas aos registros carregados nesta versão.</small>
      </article>
    </div>
    <div class="metric-grid">
      ${card('Municípios cadastrados',m.record_count||0,'Carteira de trabalho')}
      ${card('Propostas sincronizadas',totalProposals,'Fonte oficial Transferegov')}
      ${card('Contratos sincronizados',totalContracts,'Fonte oficial PNCP')}
      ${card('Obras identificadas',S.integrated?.engineering?.length||0,'ObrasGov por IBGE')}
      ${card('Valor contratado',moneyBR(S.integrated?.financial?.contract_value_total),'PNCP oficial')}
      ${card('Valor empenhado',moneyBR(S.integrated?.financial?.commitment_total),'Transferegov oficial')}
      ${card('Documentos oficiais',S.integrated?.documents?.length||0,'Com proveniência e hash')}
      ${card('Eventos na timeline',S.integrated?.timeline?.length||0,'Registros oficiais')}
      ${card('Convênios Transferegov',S.discretionary?.agreements?.length||0,'Discricionárias e Legais')}
      ${card('Contratos Transferegov',S.discretionary?.contracts?.length||0,'Vinculados por licitação oficial')}
      ${card('Pagamentos Transferegov',S.discretionary?.payments?.length||0,'Movimentações oficiais')}
      ${card('Integridade','Official-only','Sem valores ou registros inventados')}
    </div>
    <div class="truth-banner"><strong>Separação de confiança</strong><span>Municípios da carteira, propostas e contratos oficiais permanecem identificados por sua proveniência.</span></div>`;

  $('#unifiedSearchButton').onclick=searchUnifiedHome;
  $('#unifiedHomeSearch').addEventListener('keydown',e=>{if(e.key==='Enter')searchUnifiedHome()});
  $('#aiHomeButton').onclick=askHomeAI;
  $('#aiHomeInput').addEventListener('keydown',e=>{if(e.key==='Enter')askHomeAI()})
}
function searchMunicipalityHome(){S.homeQuery=$('#municipalityHomeSearch')?.value?.trim()||'';S.instrumentContractPage=1;show('instrumentos')}
function searchContractHome(){S.homeQuery=$('#contractHomeSearch')?.value?.trim()||'';S.instrumentContractPage=1;show('instrumentos')}
function searchUnifiedHome(){
  S.homeQuery=($('#unifiedHomeSearch')?.value||'').trim();
  S.instrumentContractPage=1;
  show('instrumentos')
}
function askHomeAI(){
  const input=$('#aiHomeInput');
  const q=(input?.value||'').trim();
  if(!q)return;
  const box=$('#aiConversation');
  const terms=assistantTerms(q);
  const contracts=(S.contracts||[]).filter(c=>terms.every(t=>contractHaystack(c).includes(t)));
  const proposals=(S.proposals||[]).filter(p=>terms.every(t=>proposalHaystack(p).includes(t)));
  const municipalities=(S.portfolio?.municipalities||[]).filter(m=>terms.every(t=>municipalityHaystack(m).includes(t)));
  const projects=(S.integrated?.engineering||[]).filter(project=>terms.every(t=>projectHaystack(project).includes(t)));
  const documents=(S.integrated?.documents||[]).filter(doc=>terms.every(t=>documentHaystack(doc).includes(t)));
  const paymentOrders=(S.integrated?.payment_orders||[]).filter(order=>terms.every(t=>paymentOrderHaystack(order).includes(t)));
  const accounts=(S.integrated?.accounts||[]).filter(account=>terms.every(t=>accountHaystack(account).includes(t)));
  box.innerHTML+=`<div class="notice"><strong>Você:</strong> ${esc(q)}</div>`;
  if(contracts.length||proposals.length||municipalities.length||projects.length||documents.length||paymentOrders.length||accounts.length){
    const searchTerm=terms.join(' ')||q;
    box.innerHTML+=`<div class="notice"><strong>GovParcerias AI:</strong> Encontrei ${proposals.length} proposta(s), ${contracts.length} contrato(s), ${projects.length} obra(s), ${documents.length} documento(s), ${paymentOrders.length} ordem(ns), ${accounts.length} conta(s) e ${municipalities.length} município(s) relacionados. <button id="aiViewResults">Ver resultados</button></div>`;
    const resultButton=$('#aiViewResults');
    if(resultButton)resultButton.onclick=()=>{S.homeQuery=searchTerm;show('instrumentos')}
  }else{
    box.innerHTML+=`<div class="notice"><strong>GovParcerias AI:</strong> Não encontrei evidências correspondentes na base atualmente sincronizada.</div>`
  }
  input.value='';
  box.scrollTop=box.scrollHeight
}

function filteredMunicipalities(){const q=S.municipalityQuery.trim().toLocaleLowerCase('pt-BR');return S.portfolio.municipalities.filter(m=>!q||[m.name,m.cnpj,m.ibge_code].some(x=>x.toLocaleLowerCase('pt-BR').includes(q)))}
function municipios(){const all=filteredMunicipalities(),pages=Math.max(1,Math.ceil(all.length/S.pageSize));S.municipalityPage=Math.max(1,Math.min(S.municipalityPage,pages));const start=(S.municipalityPage-1)*S.pageSize,rows=all.slice(start,start+S.pageSize);$('#content').innerHTML=head('Carteira de municípios','121 municípios cadastrados a partir da planilha fornecida, com CNPJ e código IBGE preservados exatamente como recebidos.')+`<div class="toolbar"><input id="munSearch" value="${esc(S.municipalityQuery)}" placeholder="Pesquisar município, CNPJ ou código IBGE"><button data-action="municipality-search">Pesquisar</button></div><div class="portfolio-meta"><span>${all.length} resultado(s)</span><span>Fonte: ${esc(S.portfolio.manifest.source_file)}</span><span>Validação: sem duplicidades</span></div><div class="municipality-grid">${rows.map(m=>`<button class="municipality-card" data-action="open-municipality" data-value="${esc(m.ibge_code)}"><span class="initial">${esc(m.name.slice(0,2).toUpperCase())}</span><div><strong>${esc(m.name)}</strong><small>IBGE ${esc(m.ibge_code)}</small><small>CNPJ ${esc(m.cnpj)}</small></div><b>→</b></button>`).join('')}</div><div class="pager"><button ${S.municipalityPage===1?'disabled':''} data-action="municipality-page" data-value="-1">Anterior</button><span>Página ${S.municipalityPage} de ${pages}</span><button ${S.municipalityPage===pages?'disabled':''} data-action="municipality-page" data-value="1">Próxima</button></div>`;$('#munSearch').addEventListener('keydown',e=>{if(e.key==='Enter')applyMunicipalitySearch()})}
function applyMunicipalitySearch(){S.municipalityQuery=$('#munSearch').value;S.municipalityPage=1;municipios()} function changeMunicipalityPage(d){S.municipalityPage+=d;municipios()}
function openMunicipality(code){S.selectedMunicipality=S.portfolio.municipalities.find(m=>m.ibge_code===code);municipalityProfile()}
function municipalityProfile(){
  const m=S.selectedMunicipality;
  if(!m)return show('municipios');
  const proposals=(S.proposals||[]).filter(p=>String(p.ibge_code)===String(m.ibge_code));
  const contracts=(S.contracts||[]).filter(c=>String(c.ibge_code||'')===String(m.ibge_code));
  const works=(S.integrated?.engineering||[]).filter(project=>(project.municipalities||[]).some(item=>String(item.ibge_code)===String(m.ibge_code)));
  const interruptedWorks=works.filter(project=>project.interruption_count>0||/paralisa|cancel/i.test(project.situation||''));
  $('#content').innerHTML=head(m.name,'Visão municipal com propostas Transferegov e contratos PNCP oficialmente sincronizados.',`<button data-action="show" data-value="municipios">← Voltar à carteira</button>`)
    +`<div class="profile-head"><div class="profile-mark">${esc(m.name.slice(0,2).toUpperCase())}</div><div><span class="eyebrow">Município da carteira</span><h2>${esc(m.name)}</h2><p>CNPJ ${esc(m.cnpj)} · Código IBGE ${esc(m.ibge_code)}</p></div><span class="source-pill">Carteira de trabalho</span></div>
      <div class="metric-grid">${card('Propostas oficiais',proposals.length,'Transferegov')}${card('Contratos oficiais',contracts.length,'PNCP')}${card('Obras oficiais',works.length,'ObrasGov por código IBGE')}${card('Situações de atenção',interruptedWorks.length,'Paralisada/cancelada informada pela fonte')}</div>
      <div class="tabs-inline"><button data-action="municipality-tab" data-value="propostas">Propostas</button><button data-action="municipality-tab" data-value="contratos">Contratos</button><button data-action="municipality-tab" data-value="obras">Obras</button><button data-action="municipality-tab" data-value="documentos">Documentos</button></div>
      <div id="municipalityTab"></div>
      <div class="provenance-box"><strong>Proveniência do cadastro</strong><p>Arquivo: ${esc(S.portfolio?.manifest?.source_file||'source-data/Planilha 121 municipios.xlsx')} · classificação: carteira administrativa. Propostas e contratos são identificados separadamente por suas fontes oficiais.</p></div>`;
  showMunicipalityTab('propostas')
}
function showMunicipalityTab(t){
  const m=S.selectedMunicipality;
  if(!m)return;
  if(t==='propostas'){
    const rows=(S.proposals||[]).filter(p=>String(p.ibge_code)===String(m.ibge_code));
    $('#municipalityTab').innerHTML=rows.length
      ?`<div class="portfolio-meta"><span>${rows.length} proposta(s) oficial(is)</span><span>Exibindo até 50 registros</span></div><div class="cards">${rows.slice(0,50).map(p=>proposalCard(p)).join('')}</div>`
      :empty('Nenhuma proposta oficial vinculada','A API oficial não retornou propostas para este código IBGE.');
    return
  }
  if(t==='contratos'){
    const rows=(S.contracts||[]).filter(c=>String(c.ibge_code||'')===String(m.ibge_code));
    $('#municipalityTab').innerHTML=rows.length
      ?`<div class="cards">${rows.map(c=>{const idx=(S.contracts||[]).indexOf(c);return `<article><span class="eyebrow">Contrato oficial · PNCP</span><h3>${esc(contractTitle(c))}</h3><p>${esc(contractObject(c))}</p><button data-action="open-contract" data-value="${idx}">Abrir contrato</button></article>`}).join('')}</div>`
      :empty('Nenhum contrato oficial vinculado','Nenhum contrato PNCP da base atual possui este código IBGE.');
    return
  }
  if(t==='obras'){
    const works=(S.integrated?.engineering||[]).filter(project=>(project.municipalities||[]).some(item=>String(item.ibge_code)===String(m.ibge_code)));
    $('#municipalityTab').innerHTML=works.length
      ?`<div class="cards">${works.map(project=>`<article><span class="eyebrow">ObrasGov · ${esc(project.project_id)}</span><h3>${esc(project.name)}</h3><p>${esc(clipText(project.description,180))}</p><small>Situação: ${esc(project.situation)} · Contratos: ${project.contract_count||0} · Empenhos: ${project.commitment_count||0} · Execuções: ${project.physical_execution_count||0}</small></article>`).join('')}</div>`
      :empty('Nenhuma obra oficial vinculada','A consulta territorial ObrasGov não retornou projeto para este código IBGE.');
    return
  }
  $('#municipalityTab').innerHTML=empty('Nenhum documento oficial vinculado','A plataforma não criará registros sintéticos para preencher esta área.')
}
function territorial(){
  const municipalities=S.portfolio?.municipalities||[];
  const proposals=S.proposals||[];
  const contracts=S.contracts||[];
  const projects=S.integrated?.engineering||[];
  const summaries=municipalities.map(m=>{
    const municipalContracts=contracts.filter(row=>String(row.ibge_code||'')===String(m.ibge_code));
    const municipalProjects=projects.filter(project=>(project.municipalities||[]).some(item=>String(item.ibge_code)===String(m.ibge_code)));
    return {
      ...m,
      proposals:proposals.filter(row=>String(row.ibge_code)===String(m.ibge_code)).length,
      contracts:municipalContracts.length,
      contractValue:municipalContracts.reduce((total,row)=>total+(Number(row.valor_global)||0),0),
      projects:municipalProjects.length,
      attention:municipalProjects.filter(project=>project.interruption_count>0||/paralisa|cancel/i.test(project.situation||'')).length
    }
  });
  const ranked=[...summaries].sort((a,b)=>(b.contracts+b.proposals+b.projects)-(a.contracts+a.proposals+a.projects)||a.name.localeCompare(b.name,'pt-BR'));
  const withContracts=summaries.filter(row=>row.contracts>0).length;
  const withProjects=summaries.filter(row=>row.projects>0).length;
  const totalValue=summaries.reduce((total,row)=>total+row.contractValue,0);
  $('#content').innerHTML=head('Gestão territorial e municipal','Consolidação rastreável das fontes oficiais já sincronizadas, limitada aos 121 municípios.')
    +`<div class="metric-grid">${card('Carteira atual','121 municípios','Recorte administrativo')}${card('Com contratos PNCP',withContracts,'Código IBGE oficial')}${card('Com projetos ObrasGov',withProjects,'Geometria por código IBGE')}${card('Valor contratual',moneyBR(totalValue),'Soma dos contratos PNCP carregados')}</div>
      <div class="cards"><article><h3>Carteira completa</h3><p>Consulte propostas, contratos e obras de cada município.</p><button data-action="show" data-value="municipios">Explorar municípios</button></article></div>
      <div class="portfolio-meta"><span>Comparação dos 121 municípios</span><span>Exibindo 30 com maior cobertura sincronizada</span><span>Sem classificação subjetiva</span></div>
      <div class="cards">${ranked.slice(0,30).map(row=>`<article><span class="eyebrow">IBGE ${esc(row.ibge_code)}</span><h3>${esc(row.name)}</h3><p>Propostas: ${row.proposals} · Contratos: ${row.contracts} · Obras: ${row.projects}</p><small>Valor contratual: ${moneyBR(row.contractValue)} · Situações de atenção na fonte: ${row.attention}</small><button data-action="open-municipality" data-value="${esc(row.ibge_code)}">Abrir município</button></article>`).join('')}</div>`
}
function normalizeSearch(v){
  return String(v??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('pt-BR').replace(/[^\p{L}\p{N}]+/gu,' ').replace(/\s+/g,' ').trim()
}
function digitsOnly(v){return String(v??'').replace(/\D/g,'')}
function moneyBR(v){
  if(v===null||v===undefined||v==='')return 'Não informado pela fonte';
  const n=Number(v);
  return Number.isFinite(n)?n.toLocaleString('pt-BR',{style:'currency',currency:'BRL'}):esc(v)
}
function contractHaystack(c){
  const raw=[c.source_record_id,c.numero,c.number,c.numeroContratoEmpenho,c.numeroConvenio,c.numero_convenio,c.codigoConvenio,c.codigo_convenio,c.ano,c.processo,c.objeto,c.objetoContrato,c.municipality_name,c.municipioNome,c.municipality_cnpj,c.orgao_cnpj,c.orgao_nome,c.fornecedor_nome,c.fornecedor_documento,c.nomeRazaoSocialFornecedor,c.niFornecedor,c.numeroControlePNCP,c.orgaoEntidade?.cnpj,c.orgaoEntidade?.razaoSocial,c.unidadeOrgao?.nomeUnidade].filter(Boolean).join(' ');
  return normalizeSearch(raw)+' '+digitsOnly(raw)
}
function primarySearchScore(value,query){
  const q=normalizeSearch(query),digits=digitsOnly(query),number=normalizeSearch([value.numero,value.number,value.numeroContratoEmpenho,value.numeroConvenio,value.numero_convenio,value.codigoConvenio,value.codigo_convenio,value.numeroControlePNCP].filter(Boolean).join(' '));
  const municipality=normalizeSearch([value.municipality_name,value.municipioNome,value.name].filter(Boolean).join(' '));
  const cnpj=digitsOnly([value.municipality_cnpj,value.cnpj,value.orgao_cnpj].filter(Boolean).join(' '));
  const ibge=digitsOnly(value.ibge_code);
  if(q&&number.includes(q)||digits&&digits.length>3&&number.includes(digits))return 5;
  if(q&&municipality.includes(q))return 4;
  if(digits&&digits.length>5&&cnpj.includes(digits))return 3;
  if(digits&&digits.length>5&&ibge.includes(digits))return 2;
  return 1
}
function municipalityHaystack(m){
  const raw=[m.name,m.cnpj,m.ibge_code].filter(Boolean).join(' ');
  return normalizeSearch(raw)+' '+digitsOnly(raw)
}
function clipText(v,limit=260){
  const text=String(v??'Não informado pela fonte');
  return text.length>limit?text.slice(0,limit).trim()+'…':text
}
function proposalHaystack(p){
  const raw=[p.source_record_id,p.id_proposta,p.id_programa,p.municipality_name,p.municipality_cnpj,p.ibge_code,p.receiver_name,p.receiver_cnpj,p.object,p.status,p.proposal_date].filter(Boolean).join(' ');
  return normalizeSearch(raw)+' '+digitsOnly(raw)
}
function projectHaystack(project){
  const municipalities=(project.municipalities||[]).flatMap(row=>[row.name,row.ibge_code]);
  const raw=[project.project_id,project.name,project.description,project.situation,project.nature,project.species,project.organization,...municipalities].filter(Boolean).join(' ');
  return normalizeSearch(raw)+' '+digitsOnly(raw)
}
function documentHaystack(doc){
  const raw=[doc.document_id,doc.partnership_id,doc.number,doc.document_type,doc.status,doc.creditor_id,doc.creditor_name,doc.observation,doc.commitment_number].filter(Boolean).join(' ');
  return normalizeSearch(raw)+' '+digitsOnly(raw)
}
function paymentOrderHaystack(order){
  const raw=[order.payment_order_id,order.document_id,order.number,order.status,order.bank_order_number,order.observation].filter(Boolean).join(' ');
  return normalizeSearch(raw)+' '+digitsOnly(raw)
}
function accountHaystack(account){
  const raw=[account.account_id,account.partnership_id,account.type,account.name,account.status,account.bank,account.account_number,account.branch_number,account.branch_name,account.branch_municipality,account.branch_state].filter(Boolean).join(' ');
  return normalizeSearch(raw)+' '+digitsOnly(raw)
}
function queryMatches(haystack,q){
  const normalized=normalizeSearch(q);
  const digits=digitsOnly(q);
  if(!normalized&&!digits)return true;
  const tokens=normalized.split(' ').filter(Boolean);
  const textualTokens=tokens.filter(token=>!/\d/.test(token));
  const textMatches=textualTokens.every(token=>haystack.includes(token));
  if(textualTokens.length&&digits)return textMatches&&haystack.includes(digits);
  if(textualTokens.length)return textMatches;
  return tokens.every(token=>haystack.includes(token))||(digits&&haystack.includes(digits))
}
function assistantTerms(query){
  const ignored=new Set(['mostre','quais','existe','contrato','contratos','municipio','municipios','sobre','para','com','numero','obra','obras','documento','documentos','ordem','ordens','pagamento','pagamentos','proposta','propostas','conta','contas','banco','bancos','agencia','agencias','de','do','da','dos','das','em']);
  return normalizeSearch(query).split(/\s+/).filter(token=>token.length>2&&!ignored.has(token))
}
function contractTitle(c){return c.numero||c.number||c.numeroContratoEmpenho||c.source_record_id||'Não informado pela fonte'}
function contractMunicipality(c){return c.municipality_name||c.municipioNome||c.orgao_nome||c.orgaoEntidade?.razaoSocial||'Não informado pela fonte'}
function contractObject(c){return c.objeto||c.objetoContrato||c.object||'Não informado pela fonte'}

function instrumentos(){
  const query=S.homeQuery||'';
  const contracts=(S.contracts||[]).filter(c=>queryMatches(contractHaystack(c),query));
  const proposals=(S.proposals||[]).filter(p=>queryMatches(proposalHaystack(p),query));
  const municipalities=(S.portfolio?.municipalities||[]).filter(m=>queryMatches(municipalityHaystack(m),query));
  const projects=(S.integrated?.engineering||[]).filter(project=>queryMatches(projectHaystack(project),query));
  const documents=(S.integrated?.documents||[]).filter(doc=>queryMatches(documentHaystack(doc),query));
  const paymentOrders=(S.integrated?.payment_orders||[]).filter(order=>queryMatches(paymentOrderHaystack(order),query));
  const accounts=(S.integrated?.accounts||[]).filter(account=>queryMatches(accountHaystack(account),query));
  contracts.sort((a,b)=>primarySearchScore(b,query)-primarySearchScore(a,query));
  municipalities.sort((a,b)=>primarySearchScore(b,query)-primarySearchScore(a,query));
  proposals.sort((a,b)=>primarySearchScore(b,query)-primarySearchScore(a,query));

  const contractPages=Math.max(1,Math.ceil(contracts.length/S.instrumentPageSize));
  S.instrumentContractPage=Math.min(S.instrumentContractPage,contractPages);
  const contractStart=(S.instrumentContractPage-1)*S.instrumentPageSize;
  const contractCards=contracts.slice(contractStart,contractStart+S.instrumentPageSize).map(c=>{
    const idx=(S.contracts||[]).indexOf(c);
    return `<article>
      <span class="eyebrow">Contrato oficial · ${esc(c.source||'PNCP')}</span>
      <h3>Contrato ${esc(contractTitle(c))}</h3>
      <p><strong>${esc(contractMunicipality(c))}</strong></p>
      <p>${esc(contractObject(c))}</p>
      <small>Processo: ${esc(c.processo||c.numeroProcesso||'Não informado pela fonte')} · Valor: ${moneyBR(c.valor_global??c.valorGlobal??c.valorInicial)}</small>
      <button class="primary" data-action="open-contract" data-value="${idx}">Consultar detalhamento</button>
    </article>`
  }).join('');
  const transferContractCards=(S.discretionary?.contracts||[]).filter(c=>!query||[c.NR_CONTRATO,c.ID_CONTRATO,c.OBJETO_CONTRATO,c.NOME_FORNECEDOR_CONTRATO].filter(Boolean).join(' ').toLocaleLowerCase('pt-BR').includes(query.toLocaleLowerCase('pt-BR'))).slice(0,50).map(c=>`<article><span class="eyebrow">Contrato Transferegov · ${esc(c.ID_CONTRATO||'Não informado pela fonte')}</span><h3>${esc(c.NR_CONTRATO||'Não informado pela fonte')}</h3><p>${esc(c.OBJETO_CONTRATO||'Não informado pela fonte')}</p><small>Fornecedor: ${esc(c.NOME_FORNECEDOR_CONTRATO||'Não informado pela fonte')} · Valor: ${moneyBR(c.VALOR_GLOBAL_CONTRATO)}</small><button class="primary" data-action="open-transfer-contract" data-value="${esc(c.ID_CONTRATO||'')}">Consultar detalhamento</button></article>`).join('');

  const proposalCards=proposals.slice(0,50).map(p=>proposalCard(p)).join('');

  const municipalityCards=municipalities.slice(0,50).map(m=>`
    <article>
      <span class="eyebrow">Município da carteira</span>
      <h3>${esc(m.name)}</h3>
      <p>CNPJ ${esc(m.cnpj)} · IBGE ${esc(m.ibge_code)}</p>
      <button data-action="open-municipality" data-value="${esc(m.ibge_code)}">Abrir município</button>
    </article>`).join('');

  const projectCards=projects.slice(0,50).map(project=>`<article>
    <span class="eyebrow">ObrasGov · ${esc(project.project_id)}</span>
    <h3>${esc(project.name)}</h3>
    <p>${esc(clipText(project.description,180))}</p>
    <small>${esc((project.municipalities||[]).map(row=>row.name).join(', '))} · Situação: ${esc(project.situation)}</small>
    <a href="${esc(project.source_url)}" target="_blank" rel="noopener noreferrer">Abrir fonte oficial</a>
  </article>`).join('');

  const documentCards=documents.slice(0,50).map(doc=>`<article>
    <span class="eyebrow">${esc(doc.document_type)} · ${esc(doc.number)}</span>
    <h3>${esc(doc.creditor_name)}</h3>
    <p>${esc(clipText(doc.observation,180))}</p>
    <small>Parceria ${esc(doc.partnership_id)} · Valor: ${moneyBR(doc.value)}</small>
    <a href="${esc(doc.source_url)}" target="_blank" rel="noopener noreferrer">Abrir fonte oficial</a>
  </article>`).join('');

  const paymentOrderCards=paymentOrders.slice(0,50).map(order=>`<article>
    <span class="eyebrow">Ordem de pagamento · ${esc(order.number)}</span>
    <h3>${moneyBR(order.value)}</h3>
    <p>${esc(clipText(order.observation,180))}</p>
    <small>Documento ${esc(order.document_id)} · Situação: ${esc(order.status)}</small>
    <a href="${esc(order.source_url)}" target="_blank" rel="noopener noreferrer">Abrir fonte oficial</a>
  </article>`).join('');

  const accountCards=accounts.slice(0,50).map(account=>`<article>
    <span class="eyebrow">${esc(account.type)} · parceria ${esc(account.partnership_id)}</span>
    <h3>${esc(account.bank)}</h3>
    <p>${esc(account.status)}</p>
    <small>Agência ${esc(account.branch_number)} ${esc(account.branch_name)} · Conta ${esc(account.account_number)}</small>
    <a href="${esc(account.source_url)}" target="_blank" rel="noopener noreferrer">Abrir fonte oficial</a>
  </article>`).join('');

  const summary=query
    ?`${proposals.length} proposta(s), ${contracts.length} contrato(s), ${projects.length} obra(s), ${documents.length} documento(s), ${paymentOrders.length} ordem(ns), ${accounts.length} conta(s) e ${municipalities.length} município(s) encontrado(s) para “${esc(query)}”.`
    :`${proposals.length} proposta(s), ${contracts.length} contrato(s), ${projects.length} obra(s), ${documents.length} documento(s), ${paymentOrders.length} ordem(ns), ${accounts.length} conta(s) e ${municipalities.length} município(s) disponíveis.`;

  $('#content').innerHTML=
    head('Consulta unificada','Ordem principal: contrato/convênio · município · CNPJ · IBGE · proposta. Obras, documentos, contas e pagamentos aparecem como evidências relacionadas.',`<button id="backToHomeButton">← Voltar</button>`)
    +`<div class="toolbar">
       <input id="contractSearch" value="${esc(query)}" placeholder="Digite qualquer termo da consulta">
       <button id="contractSearchButton">Pesquisar</button>
      </div>
      <div class="portfolio-meta"><span>${summary}</span><span>Propostas: ${(S.proposals||[]).length}</span><span>Contratos: ${(S.contracts||[]).length}</span><span>Modo: official-only</span></div>
      ${contracts.length?`<h2>Contratos oficiais</h2><div class="cards">${contractCards}</div><div class="pager"><button ${S.instrumentContractPage===1?'disabled':''} data-action="instrument-contract-page" data-value="-1">Anterior</button><span>Página ${S.instrumentContractPage} de ${contractPages} · ${contracts.length} resultado(s)</span><button ${S.instrumentContractPage===contractPages?'disabled':''} data-action="instrument-contract-page" data-value="1">Próxima</button></div>`:''}
      ${transferContractCards?`<h2>Contratos Transferegov</h2><div class="cards">${transferContractCards}</div>`:''}
      ${municipalities.length?`<h2>Municípios</h2><div class="cards">${municipalityCards}</div>`:''}
      ${proposals.length?`<h2>Propostas oficiais</h2><div class="cards">${proposalCards}</div>`:''}
      ${projects.length?`<h2>Obras oficiais</h2><div class="cards">${projectCards}</div>`:''}
      ${documents.length?`<h2>Documentos hábeis oficiais</h2><div class="cards">${documentCards}</div>`:''}
      ${paymentOrders.length?`<h2>Ordens de pagamento oficiais</h2><div class="cards">${paymentOrderCards}</div>`:''}
      ${accounts.length?`<h2>Contas de parceria oficiais</h2><div class="cards">${accountCards}</div>`:''}
      ${!proposals.length&&!contracts.length&&!projects.length&&!documents.length&&!paymentOrders.length&&!accounts.length&&!municipalities.length?empty('Nenhum resultado localizado',`A consulta por ${esc(query)} não encontrou registros oficiais na base sincronizada.`):''}`;

  $('#contractSearchButton').onclick=applyContractSearch;
  const backToHomeButton=$('#backToHomeButton');
  if(backToHomeButton)backToHomeButton.onclick=()=>show('inicio');
  $('#contractSearch').addEventListener('keydown',e=>{if(e.key==='Enter')applyContractSearch()});
  const backButton=$('#backToHomeButton');
  if(backButton)backButton.onclick=()=>show('inicio')
}
function applyContractSearch(){S.homeQuery=($('#contractSearch')?.value||'').trim();S.instrumentContractPage=1;instrumentos()}
function openMunicipalityFromSearch(code){
  S.selectedMunicipality=(S.portfolio?.municipalities||[]).find(m=>String(m.ibge_code)===String(code));
  municipalityProfile()
}
function openContractResult(index){S.selectedOfficialContract=(S.contracts||[])[index];contractDetail()}
function openTransferContract(id){const c=(S.discretionary?.contracts||[]).find(row=>String(row.ID_CONTRATO)===String(id));if(!c)return;const payments=(S.discretionary?.payments||[]).filter(row=>String(row.NR_CONVENIO)===String(c.NR_CONVENIO));$('#content').innerHTML=head(`Contrato Transferegov ${c.NR_CONTRATO||id}`,'Detalhamento oficial do contrato e movimentações relacionadas.',`<button data-action="show" data-value="instrumentos">← Voltar aos contratos</button>`)+`<div class="field-grid">${field('Identificador',c.ID_CONTRATO)}${field('Licitação',c.ID_LICITACAO)}${field('Objeto',c.OBJETO_CONTRATO)}${field('Fornecedor',c.NOME_FORNECEDOR_CONTRATO)}${field('Valor global',moneyBR(c.VALOR_GLOBAL_CONTRATO))}${field('Vigência',`${c.DATA_INICIO_VIGENCIA_CONTRATO||'Não informado pela fonte'} a ${c.DATA_FIM_VIGENCIA_CONTRATO||'Não informado pela fonte'}`)}</div><h2>Pagamentos relacionados</h2>${payments.length?`<div class="cards">${payments.map(p=>`<article><span class="eyebrow">Pagamento ${esc(p.NR_MOV_FIN||'Não informado pela fonte')}</span><h3>${moneyBR(p.VL_PAGO)}</h3><p>Convênio ${esc(p.NR_CONVENIO||'Não informado pela fonte')}</p><small>Data: ${esc(p.DATA_PAG||'Não informado pela fonte')} · Fornecedor: ${esc(p.NOME_FORNECEDOR||'Não informado pela fonte')}</small></article>`).join('')}</div>`:empty('Nenhum pagamento relacionado','A fonte oficial não informou pagamentos para este convênio.')}`}
function proposalCard(p){
  const idx=(S.proposals||[]).indexOf(p);
  return `<article>
    <span class="eyebrow">Proposta oficial · Transferegov</span>
    <h3>Proposta ${esc(p.id_proposta||p.source_record_id)}</h3>
    <p><strong>${esc(p.municipality_name)}</strong> · ${esc(p.receiver_name)}</p>
    <p>${esc(clipText(p.object))}</p>
    <small>Situação: ${esc(p.status)} · Valor: ${moneyBR(p.total_value)}</small>
    <button data-action="open-proposal" data-value="${idx}">Abrir proposta</button>
  </article>`
}
function openProposalResult(index){S.selectedOfficialProposal=(S.proposals||[])[index];proposalDetail()}
function proposalDetail(){
  const p=S.selectedOfficialProposal;
  if(!p)return show('instrumentos');
  const relation=(S.integrated?.instrument_relations||[]).find(row=>String(row.proposal_id)===String(p.id_proposta))||{};
  const fields=[
    ['Identificador da proposta',p.id_proposta],
    ['Programa',p.id_programa],
    ['Município',p.municipality_name],
    ['Código IBGE',p.ibge_code],
    ['CNPJ da carteira',p.municipality_cnpj],
    ['Ente recebedor',p.receiver_name],
    ['CNPJ do recebedor',p.receiver_cnpj],
    ['Situação',p.status],
    ['Valor total',moneyBR(p.total_value)],
    ['Data da proposta',p.proposal_date],
    ['Objeto',p.object],
    ['Fonte',p.source],
    ['URL da fonte',p.source_url],
    ['Coletado em',p.fetched_at],
    ['Hash SHA-256',p.sha256]
  ];
  $('#content').innerHTML=
    head(`Proposta ${esc(p.id_proposta)}`,'Registro oficial do Transferegov com proveniência verificável.',`<button data-action="show" data-value="instrumentos">← Voltar aos resultados</button>`)
    +`<div class="section-head"><div><span class="eyebrow">Proposta oficial</span><h2>${esc(p.municipality_name)}</h2><p>${esc(p.object)}</p></div><span class="source-pill">Transferegov</span></div>
      <div class="metric-grid">${card('Parcerias vinculadas',(relation.partnership_ids||[]).length,'id_proposta → id_parceria')}${card('Metas',relation.goal_count||0,S.integrated?.sync_status?.proposal_goals?.completed?'Carga concluída':'Carga parcial')}${card('Cronogramas',relation.schedule_count||0,'Itens oficiais')}${card('Análises',relation.analysis_count||0,S.integrated?.sync_status?.proposal_analyses?.completed?'Carga concluída':'Carga parcial')}${card('Indicadores',relation.indicator_count||0,S.integrated?.sync_status?.proposal_indicators?.completed?'Carga concluída':'Carga parcial')}${card('Distribuições de recursos',relation.resource_count||0,S.integrated?.sync_status?.proposal_resources?.completed?'Carga concluída':'Carga parcial')}${card('Empenhos',relation.commitment_count||0,'Via id_parceria')}${card('Documentos hábeis',relation.payable_document_count||0,S.integrated?.sync_status?.payable_documents?.completed?'Carga concluída':'Carga parcial')}${card('Ordens de pagamento',relation.payment_order_count||0,'Via id_documento_habil')}${card('Contas',relation.account_count||0,S.integrated?.sync_status?.partnership_accounts?.completed?'Carga concluída':'Carga parcial')}${card('Lançamentos bancários',relation.bank_statement_count||0,S.integrated?.sync_status?.bank_statements?.completed?'Carga concluída':'Carga parcial')}</div>
      <div class="field-grid">${fields.map(([label,value])=>`<div class="field"><label>${esc(label)}</label><strong>${label.includes('Valor')?value:esc(value||'Não informado pela fonte')}</strong></div>`).join('')}</div>
      ${(relation.goals||[]).length?`<h2>Metas oficiais</h2><div class="cards">${relation.goals.map(goal=>`<article><span class="eyebrow">Meta ${esc(goal.code)} · ${goal.stage_count||0} etapa(s)</span><h3>${esc(goal.name)}</h3><p>${esc(clipText(goal.description,260))}</p><a href="${esc(goal.source_url)}" target="_blank" rel="noopener noreferrer">Abrir fonte oficial</a></article>`).join('')}</div>`:''}
      ${(relation.analyses||[]).length?`<h2>Análises oficiais</h2><div class="cards">${relation.analyses.map(analysis=>`<article><span class="eyebrow">${esc(analysis.recorded_at)} · ${esc(analysis.phase)}</span><h3>${esc(analysis.result)}</h3><p>${esc(clipText(analysis.opinion,300))}</p><small>${analysis.analysis_type_count||0} tipo(s) informado(s)</small><a href="${esc(analysis.source_url)}" target="_blank" rel="noopener noreferrer">Abrir fonte oficial</a></article>`).join('')}</div>`:''}
      ${(relation.indicators||[]).length?`<h2>Indicadores oficiais</h2><div class="cards">${relation.indicators.map(indicator=>`<article><span class="eyebrow">${esc(indicator.unit)}</span><h3>${esc(indicator.name)}</h3><p>${esc(indicator.expected_result)}</p><small>Valor informado: ${esc(indicator.value)}</small><a href="${esc(indicator.source_url)}" target="_blank" rel="noopener noreferrer">Abrir fonte oficial</a></article>`).join('')}</div>`:''}
      ${(relation.resources||[]).length?`<h2>Distribuição oficial de recursos</h2><div class="cards">${relation.resources.map(resource=>`<article><span class="eyebrow">${esc(resource.distribution_type)} · ${esc(resource.gnd)}</span><h3>${moneyBR(resource.value)}</h3><p>${esc(resource.parliamentarian)} · Emenda ${esc(resource.amendment_number)}</p><small>Tipo: ${esc(resource.amendment_type)}</small><a href="${esc(resource.source_url)}" target="_blank" rel="noopener noreferrer">Abrir fonte oficial</a></article>`).join('')}</div>`:''}`
}
function contractDetail(){
  const c=S.selectedOfficialContract;
  if(!c)return show('instrumentos');
  const fields=[
    ['Número do contrato',contractTitle(c)],
    ['Identificador PNCP',c.source_record_id||c.numeroControlePNCP||'Não informado pela fonte'],
    ['Município',contractMunicipality(c)],
    ['CNPJ do órgão',c.municipality_cnpj||c.orgao_cnpj||c.orgaoEntidade?.cnpj||'Não informado pela fonte'],
    ['Processo',c.processo||c.numeroProcesso||'Não informado pela fonte'],
    ['Fornecedor',c.fornecedor_nome||c.nomeRazaoSocialFornecedor||c.fornecedor?.nome||'Não informado pela fonte'],
    ['CNPJ/CPF do fornecedor',c.fornecedor_documento||c.niFornecedor||'Não informado pela fonte'],
    ['Valor global',moneyBR(c.valor_global??c.valorGlobal??c.valorInicial)],
    ['Valor acumulado',moneyBR(c.valor_acumulado??c.valorAcumulado)],
    ['Assinatura',c.data_assinatura||c.dataAssinatura||'Não informado pela fonte'],
    ['Vigência inicial',c.vigencia_inicio||c.dataVigenciaInicio||'Não informado pela fonte'],
    ['Vigência final',c.vigencia_fim||c.dataVigenciaFim||'Não informado pela fonte'],
    ['Objeto',contractObject(c)],
    ['Fonte',c.source||'PNCP'],
    ['URL da fonte',c.source_url||'Não informado pela fonte'],
    ['Coletado em',c.fetched_at||'Não informado pela fonte'],
    ['Hash SHA-256',c.sha256||'Não informado pela fonte']
  ];
  $('#content').innerHTML=
    head(`Contrato ${esc(contractTitle(c))}`,'Registro oficial sincronizado e apresentado com sua proveniência.',`<button data-action="show" data-value="instrumentos">← Voltar aos resultados</button>`)
    +`<div class="section-head"><div><span class="eyebrow">Contrato oficial</span><h2>${esc(contractMunicipality(c))}</h2><p>${esc(contractObject(c))}</p></div><span class="source-pill">${esc(c.source||'PNCP')}</span></div>
      <div class="field-grid">${fields.map(([label,value])=>`<div class="field"><label>${esc(label)}</label><strong>${label.includes('Valor')?value:esc(value)}</strong></div>`).join('')}</div>`
}

function dossie(){
  const c=S.selectedOfficialContract;
  if(!c){
    const q=(S.dossierQuery||'').trim();
    const contracts=(S.contracts||[]).filter(contract=>queryMatches(contractHaystack(contract),q));
    const cards=contracts.slice(0,100).map(contract=>{const index=(S.contracts||[]).indexOf(contract);return `<article><span class="eyebrow">Contrato oficial · PNCP</span><h3>${esc(contractTitle(contract))}</h3><p><strong>${esc(contractMunicipality(contract))}</strong></p><p>${esc(clipText(contractObject(contract),180))}</p><small>Processo: ${esc(contract.processo||contract.numeroProcesso||'Não informado pela fonte')} · PNCP: ${esc(contract.source_record_id||'Não informado pela fonte')}</small><button data-action="select-dossier-contract" data-value="${index}">Abrir dossiê</button></article>`}).join('');
    $('#content').innerHTML=head('Dossiê integral por contrato','Pesquise por número de contrato/convênio, município, CNPJ, processo ou identificador PNCP.')+`<div class="toolbar"><input id="dossierSearch" value="${esc(q)}" placeholder="Contrato, convênio, município, CNPJ ou PNCP"><button data-action="dossier-search">Pesquisar</button></div><div class="portfolio-meta"><span>${contracts.length} contrato(s) encontrado(s)</span><span>Fonte: PNCP</span><span>Campos ausentes: Não informado pela fonte</span></div><div class="cards">${cards||empty('Nenhum contrato encontrado','Tente o número do contrato, município ou identificador oficial.')}</div>`;
    $('#dossierSearch').addEventListener('keydown',e=>{if(e.key==='Enter')applyDossierSearch()});
    return
  }
  const sections=[
    ['identificacao','Identificação'],
    ['financeiro','Financeiro'],
    ['vigencia','Vigência'],
    ['proveniencia','Proveniência']
  ];
  $('#content').innerHTML=head(`Dossiê do contrato ${esc(contractTitle(c))}`,'Dados oficiais sincronizados do PNCP.',`<button data-action="show" data-value="instrumentos">← Consulta unificada</button>`)
    +`<div class="dossier"><aside class="tabs">${sections.map(([id,title])=>`<button class="${S.selectedSection===id?'active':''}" data-action="select-section" data-value="${id}">${title}</button>`).join('')}</aside><section class="dossier-main">${sectionView()}</section></div>`
}
function applyDossierSearch(){S.dossierQuery=$('#dossierSearch')?.value?.trim()||'';S.selectedOfficialContract=null;dossie()}
function selectSection(id){S.selectedSection=id;dossie()}
function field(label,value){return `<div class="field"><label>${esc(label)}</label><strong>${esc(value??'Não informado pela fonte')}</strong></div>`}
function sectionView(){
  const c=S.selectedOfficialContract;
  if(!c)return empty('Contrato não selecionado','Selecione um contrato oficial para abrir o dossiê.');
  const sections={
    identificacao:[
      ['Identificador PNCP',c.source_record_id],['Número',contractTitle(c)],['Município',contractMunicipality(c)],
      ['CNPJ do órgão',c.orgao_cnpj],['Órgão',c.orgao_nome],['Processo',c.processo],['Fornecedor',c.fornecedor_nome],
      ['Documento do fornecedor',c.fornecedor_documento],['Objeto',contractObject(c)]
    ],
    financeiro:[
      ['Valor inicial',moneyBR(c.valor_inicial)],['Valor global',moneyBR(c.valor_global)],['Valor acumulado',moneyBR(c.valor_acumulado)]
    ],
    vigencia:[
      ['Assinatura',c.data_assinatura],['Início da vigência',c.vigencia_inicio],['Fim da vigência',c.vigencia_fim],
      ['Publicação no PNCP',c.data_publicacao_pncp],['Atualização na fonte',c.data_atualizacao]
    ],
    proveniencia:[
      ['Fonte',c.source],['URL oficial',c.source_url],['Coletado em',c.fetched_at],['Hash SHA-256',c.sha256]
    ]
  };
  const current=sections[S.selectedSection]||sections.identificacao;
  return `<div class="section-head"><div><span class="eyebrow">Contrato oficial</span><h2>${esc(contractTitle(c))}</h2><p>${esc(contractMunicipality(c))}</p></div><span class="source-pill">PNCP</span></div><div class="field-grid">${current.map(([label,value])=>field(label,value)).join('')}</div>`
}
function generic(title,desc,detail){$('#content').innerHTML=head(title,desc)+empty(detail)}
function financeiro(){
  const f=S.integrated?.financial||{records:{}};
  const d=S.discretionary||{};
  const r=f.records||{};
  const accounts=S.integrated?.accounts||[];
  const commitmentSync=S.integrated?.sync_status?.commitments||{};
  const commitmentLabel=`${r.commitments||0} registro(s)${commitmentSync.completed?'':' · sincronização parcial'}`;
  const orderSync=S.integrated?.sync_status?.payment_orders||{};
  const orderLabel=`${r.payment_orders||0} registro(s)${orderSync.completed?'':' · sincronização parcial'}`;
  const accountSync=S.integrated?.sync_status?.partnership_accounts||{};
  const accountLabel=`${r.partnership_accounts||0}${accountSync.completed?'':' · sincronização parcial'}`;
  const statementSync=S.integrated?.sync_status?.bank_statements||{};
  const statementLabel=`${r.bank_statements||0} lançamento(s)${statementSync.completed?'':' · sincronização parcial'}`;
  $('#content').innerHTML=head('Inteligência financeira','Valores agregados exclusivamente dos registros oficiais sincronizados.')
    +`<div class="metric-grid">${card('Valor global dos contratos',moneyBR(f.contract_value_total),'PNCP')}${card('Cronograma de desembolso',moneyBR(f.scheduled_disbursement_total),`${r.schedules||0} registro(s)`)}${card('Empenhos',moneyBR(f.commitment_total),commitmentLabel)}${card('Ordens de pagamento',moneyBR(f.payment_order_total),orderLabel)}${card('Pagamentos Transferegov',d.payments?.length||0,'Download oficial filtrado')}${card('Desembolsos Transferegov',d.disbursements?.length||0,'Download oficial filtrado')}</div>
      <div class="cards"><article><h3>Empenhos de obras</h3><p>${moneyBR(f.obrasgov_commitment_total)}</p><small>${r.project_commitments||0} registro(s) ObrasGov; não somados aos empenhos de parcerias</small></article><article><h3>Documentos hábeis</h3><p>${moneyBR(f.payable_document_total)}</p><small>${r.payable_documents||0} registro(s) oficial(is)</small></article><article><h3>Recursos distribuídos em propostas</h3><p>${moneyBR(f.proposal_resource_total)}</p><small>${r.proposal_resources||0} registro(s) Transferegov</small></article><article><h3>Planos de ação especiais</h3><p>${r.special_action_plans||0}</p><small>Transferências Especiais filtradas por CNPJ da carteira</small></article><article><h3>Programas especiais</h3><p>${r.special_programs||0}</p><small>Programas oficiais referenciados pelos planos da carteira</small></article><article><h3>Análises de planos de trabalho</h3><p>${r.special_work_plan_analyses||0}</p><small>Análises oficiais vinculadas por ID do plano</small></article><article><h3>Histórico de pagamentos</h3><p>${r.special_payment_history||0}</p><small>Eventos oficiais vinculados às ordens bancárias</small></article><article><h3>Documentos especiais</h3><p>${r.special_documents||0}</p><small>Documentos hábeis relacionados por empenho oficial</small></article><article><h3>Ordens especiais</h3><p>${r.special_orders||0}</p><small>Ordens bancárias relacionadas por documento oficial</small></article><article><h3>Relatórios especiais</h3><p>${(r.special_reports||0)+(r.special_new_reports||0)}</p><small>Relatórios de gestão oficiais</small></article><article><h3>Finalidades e metas especiais</h3><p>${(r.special_purposes||0)+(r.special_goals||0)}</p><small>Relacionadas aos executores oficiais</small></article><article><h3>Contas de parceria</h3><p>${accountLabel}</p><small>Saldos exibidos individualmente porque as datas de referência podem divergir</small></article><article><h3>Movimentação bancária líquida</h3><p>${moneyBR(f.bank_movement_total)}</p><small>${statementLabel}</small><small>Créditos: ${moneyBR(f.bank_credit_total)} · Débitos: ${moneyBR(f.bank_debit_total)}</small></article><article><h3>Contratos considerados</h3><p>${r.contracts||0}</p><small>Registros PNCP com valor informado pela fonte</small></article></div>
      ${accounts.length?`<h2>Contas oficiais das parcerias</h2><div class="cards">${accounts.slice(0,100).map(account=>`<article><span class="eyebrow">${esc(account.type)} · parceria ${esc(account.partnership_id)}</span><h3>${esc(account.bank)}</h3><p>${esc(account.status)}</p><small>Agência: ${esc(account.branch_number)} ${esc(account.branch_name)} · Conta: ${esc(account.account_number)}</small><small>Saldo corrente: ${moneyBR(account.current_balance)} em ${esc(account.current_balance_at)} · Investimento: ${moneyBR(account.investment_balance)} em ${esc(account.investment_balance_at)}</small><small>Extratos: ${account.bank_statement_count||0} · Créditos: ${moneyBR(account.bank_credit_total)} · Débitos: ${moneyBR(account.bank_debit_total)}</small><small>Período dos lançamentos: ${esc(account.bank_statement_first_at)} a ${esc(account.bank_statement_last_at)}</small><a href="${esc(account.source_url)}" target="_blank" rel="noopener noreferrer">Abrir fonte oficial</a></article>`).join('')}</div>`:''}
      ${!(r.schedules||r.commitments||r.payment_orders)?empty('Execução financeira do Transferegov em sincronização','Os valores PNCP já estão disponíveis; cronogramas, empenhos e pagamentos serão incorporados por checkpoint.'):''}`
}
function engenharia(){
  const projects=S.integrated?.engineering||[];
  const geometryCount=S.integrated?.counts?.obrasgov_geometries||0;
  $('#content').innerHTML=head('Obras e engenharia','Projetos de investimento localizados oficialmente pelo código IBGE no ObrasGov.')
    +`<div class="metric-grid">${card('Projetos identificados',projects.length,'ObrasGov')}${card('Geometrias oficiais',geometryCount,'Filtro cod_ibge')}${card('Com contratos de obra',projects.filter(row=>row.contract_count>0).length,'Vínculo oficial por projeto')}${card('Com execução física',projects.filter(row=>row.physical_execution_count>0).length,'Carga parcial quando indicada pela fonte')}</div>
      <div class="portfolio-meta"><span>${projects.length} projeto(s) na carteira</span><span>Exibindo até 200</span><span>Sem consulta nacional</span></div>
      ${projects.length?`<div class="cards">${projects.slice(0,200).map(project=>`<article><span class="eyebrow">ObrasGov · ${esc(project.project_id)}</span><h3>${esc(project.name)}</h3><p>${esc(clipText(project.description,180))}</p><small>${esc(project.municipalities.map(m=>m.name).join(', '))} · Situação: ${esc(project.situation)}</small><small>Contratos: ${project.contract_count||0} · Empenhos: ${project.commitment_count||0} · Execuções: ${project.physical_execution_count||0} · Interrupções: ${project.interruption_count||0}</small></article>`).join('')}</div>`:empty('Nenhum projeto ObrasGov sincronizado','A coleta territorial por código IBGE ainda não retornou registros.')}`
}
function documentos(){
  const contracts=(S.contracts||[]).slice(0,100);
  const payableDocuments=S.integrated?.documents||[];
  const paymentOrders=S.integrated?.payment_orders||[];
  const financial=S.integrated?.financial||{records:{}};
  const records=financial.records||{};
  const documentSync=S.integrated?.sync_status?.payable_documents||{};
  const documentStatus=documentSync.completed?'Carga concluída':`${documentSync.processed_roots||0}/${documentSync.roots_total||1935} parcerias`;
  const orderSync=S.integrated?.sync_status?.payment_orders||{};
  const orderStatus=orderSync.completed?'Carga concluída':`${orderSync.processed_roots||0}/${orderSync.roots_total||payableDocuments.length} documentos`;
  $('#content').innerHTML=head('Centro de documentos e proveniência','Referências oficiais, URLs de origem, horários de coleta e hashes verificáveis.')
    +`<div class="metric-grid">${card('Registros avaliados',S.integrated?.integrity?.records_assessed||0,'PNCP + Transferegov + ObrasGov')}${card('Contratos PNCP',(S.contracts||[]).length,'Exibindo até 100 referências')}${card('Propostas Transferegov',(S.proposals||[]).length,'Hashes preservados')}${card('Documentos hábeis',records.payable_documents||0,documentStatus)}</div>
      <h2>Documentos hábeis do Transferegov</h2>
      ${payableDocuments.length?`<div class="cards">${payableDocuments.slice(0,100).map(doc=>`<article><span class="eyebrow">${esc(doc.document_type)} · ${esc(doc.number)}</span><h3>${esc(doc.creditor_name)}</h3><p>${esc(clipText(doc.observation,180))}</p><small>Emissão: ${esc(doc.issued_at)} · Valor: ${moneyBR(doc.value)} · Situação: ${esc(doc.status)}</small><small>Parceria ${esc(doc.partnership_id)} · Ordens: ${doc.payment_order_count||0} · SHA-256: ${esc(doc.sha256)}</small><a href="${esc(doc.source_url)}" target="_blank" rel="noopener noreferrer">Abrir fonte oficial</a></article>`).join('')}</div>`:empty('Nenhum documento hábil oficial carregado')}
      <h2>Ordens de pagamento do Transferegov <small>· ${orderStatus}</small></h2>
      ${paymentOrders.length?`<div class="cards">${paymentOrders.slice(0,100).map(order=>`<article><span class="eyebrow">Ordem ${esc(order.number)}</span><h3>${moneyBR(order.value)}</h3><p>${esc(clipText(order.observation,180))}</p><small>Documento ${esc(order.document_id)} · Situação: ${esc(order.status)} · Emissão: ${esc(order.issued_at)}</small><small>Ordem bancária: ${esc(order.bank_order_number)} · SHA-256: ${esc(order.sha256)}</small><a href="${esc(order.source_url)}" target="_blank" rel="noopener noreferrer">Abrir fonte oficial</a></article>`).join('')}</div>`:empty('Nenhuma ordem de pagamento oficial carregada')}
      <h2>Contratos PNCP com proveniência</h2>
      <div class="cards">${contracts.map(c=>`<article><span class="eyebrow">PNCP · contrato ${esc(contractTitle(c))}</span><h3>${esc(contractMunicipality(c))}</h3><p>${esc(clipText(contractObject(c),160))}</p><small>SHA-256: ${esc(c.sha256||'Não informado pela fonte')}</small><button data-action="open-contract" data-value="${(S.contracts||[]).indexOf(c)}">Ver proveniência</button></article>`).join('')}</div>`
}
function timeline(){
  const rows=S.integrated?.timeline||[];
  $('#content').innerHTML=head('Timeline integrada','Eventos ordenados por datas fornecidas pelas fontes oficiais.')
    +`<div class="portfolio-meta"><span>${rows.length} evento(s) verificável(is)</span><span>Exibindo até 200</span></div>
      ${rows.length?`<div class="cards">${rows.slice(0,200).map(row=>`<article><span class="eyebrow">${esc(row.occurred_at)} · ${esc(row.event_type)}</span><h3>${esc(row.title)}</h3><p>${esc(row.municipality_name)}</p>${row.detail?`<p>${esc(clipText(row.detail,220))}</p>`:''}<small>Entidade: ${esc(row.entity)} ${esc(row.entity_id)}</small>${row.source_url&&row.source_url!=='Não informado pela fonte'?`<a href="${esc(row.source_url)}" target="_blank" rel="noopener noreferrer">Abrir fonte oficial</a>`:''}</article>`).join('')}</div>`:empty('Nenhum evento oficial carregado')}`
}
function riscos(){
  const integrity=S.integrated?.integrity||{rules:[]};
  const signals=integrity.signals||[];
  const sync=S.integrated?.sync_status||{};
  const syncLabels={
    partnerships:'Parcerias',proposal_goals:'Metas',disbursement_schedule:'Cronogramas',
    proposal_analyses:'Análises',proposal_indicators:'Indicadores',
    proposal_resources:'Distribuições de recursos',commitments:'Empenhos',
    payable_documents:'Documentos hábeis',partnership_accounts:'Contas de parceria',
    payment_orders:'Ordens de pagamento',bank_statements:'Extratos bancários',
    physical_execution:'Execução física',project_contracts:'Contratos de obras',
    project_commitments:'Empenhos de obras',project_interruptions:'Histórico de interrupções',
    feasibility_studies:'Estudos de viabilidade'
  };
  $('#content').innerHTML=head('Risco e conformidade','Controles determinísticos sobre chaves e relacionamentos oficiais; nenhuma inferência subjetiva.')
    +`<div class="metric-grid">${card('Registros avaliados',integrity.records_assessed||0,'Grafos oficiais')}${card('Ambiguidades rejeitadas',integrity.ambiguous_relationships||0,'Não entram na base publicada')}${card('Regras ativas',(integrity.rules||[]).length,'Determinísticas')}${card('Sinais operacionais',signals.reduce((sum,signal)=>sum+(signal.count||0),0),'Não presumem irregularidade')}</div>
      <h2>Estado dos conectores</h2><div class="cards">${Object.entries(sync).map(([id,status])=>`<article><span class="eyebrow">${esc(id)}</span><h3>${esc(syncLabels[id]||id)}</h3><p>${status.completed?'Concluído':status.roots_total?'Parcial ou interrompido':'Ainda não iniciado'}</p><small>Raízes: ${status.processed_roots||0}/${status.roots_total||0} · Registros: ${status.records||0} · Erros: ${status.errors||0}</small></article>`).join('')}</div>
      <h2>Integridade das relações</h2><div class="cards">${(integrity.rules||[]).map(rule=>`<article><span class="eyebrow">Regra ${esc(rule.id)}</span><h3>${rule.violations||0} violação(ões)</h3><p>${esc(rule.description)}</p></article>`).join('')}</div>
      <h2>Sinais baseados na fonte</h2><div class="cards">${signals.map(signal=>`<article><span class="eyebrow">${esc(signal.id)}</span><h3>${signal.count||0} registro(s)</h3><p>${esc(signal.label)}</p><small>${esc(signal.basis)} ${esc(signal.classification)}</small></article>`).join('')}</div>`
}
function copiloto(){$('#content').innerHTML=head('Copiloto territorial e contratual','O mesmo agente atende perguntas operacionais por contrato e perguntas gerenciais por município ou território.')+`<div class="ai-policy"><h2>Escopo de consulta</h2><ol><li>Contrato individual: detalhe técnico, financeiro, documental e histórico.</li><li>Município: consolidação de todos os contratos oficialmente vinculados.</li><li>Território: agregação rastreável dos municípios e contratos componentes.</li><li>Ausência de evidência: resposta explícita, sem inferência factual.</li></ol><button class="primary" data-action="open-chat">Abrir copiloto</button></div>`}
function openChat(){$('#chat').classList.add('open')} function closeChat(){$('#chat').classList.remove('open')} function openPalette(){$('#palette').classList.add('open');setTimeout(()=>$('#paletteInput')?.focus(),20)} function closePalette(){$('#palette').classList.remove('open')}
function assistantQuery(){
  const input=$('#chatInput');
  const query=(input?.value||'').trim();
  if(!query)return;
  const terms=assistantTerms(query);
  const contracts=(S.contracts||[]).filter(c=>terms.every(term=>contractHaystack(c).includes(term)));
  const proposals=(S.proposals||[]).filter(p=>terms.every(term=>proposalHaystack(p).includes(term)));
  const municipalities=(S.portfolio?.municipalities||[]).filter(m=>terms.every(term=>municipalityHaystack(m).includes(term)));
  const projects=(S.integrated?.engineering||[]).filter(project=>terms.every(term=>projectHaystack(project).includes(term)));
  const documents=(S.integrated?.documents||[]).filter(doc=>terms.every(term=>documentHaystack(doc).includes(term)));
  const paymentOrders=(S.integrated?.payment_orders||[]).filter(order=>terms.every(term=>paymentOrderHaystack(order).includes(term)));
  const accounts=(S.integrated?.accounts||[]).filter(account=>terms.every(term=>accountHaystack(account).includes(term)));
  const body=$('#chatBody');
  body.innerHTML+=`<div class="notice"><strong>Você:</strong> ${esc(query)}</div><div class="notice"><strong>Copiloto:</strong> ${proposals.length} proposta(s), ${contracts.length} contrato(s), ${projects.length} obra(s), ${documents.length} documento(s), ${paymentOrders.length} ordem(ns), ${accounts.length} conta(s) e ${municipalities.length} município(s) encontrado(s) na base oficial sincronizada.</div>`;
  input.value='';
  body.scrollTop=body.scrollHeight
}
// Vistas operacionais: contrato/município primeiro, proposta como referência complementar.
function municipalityContracts(m){return (S.contracts||[]).filter(c=>String(c.ibge_code||'')===String(m.ibge_code))}
function municipalityDocuments(m){return (S.integrated?.documents||[]).filter(d=>String(d.ibge_code||d.municipality_ibge||'')===String(m.ibge_code))}
function municipalityProfile(){const m=S.selectedMunicipality;if(!m)return show('municipios');const contracts=municipalityContracts(m),works=(S.integrated?.engineering||[]).filter(p=>(p.municipalities||[]).some(x=>String(x.ibge_code)===String(m.ibge_code))),docs=municipalityDocuments(m),props=(S.proposals||[]).filter(p=>String(p.ibge_code)===String(m.ibge_code));$('#content').innerHTML=head(m.name,'Visão municipal priorizada por contratos, convênios e obras oficiais.',`<button data-action="show" data-value="municipios">← Voltar</button>`)+`<div class="profile-head"><div class="profile-mark">${esc(m.name.slice(0,2).toUpperCase())}</div><div><span class="eyebrow">Município da carteira</span><h2>${esc(m.name)}</h2><p>CNPJ ${esc(m.cnpj)} · IBGE ${esc(m.ibge_code)}</p></div></div><div class="metric-grid">${card('Contratos/convênios',contracts.length,'PNCP')}${card('Obras',works.length,'ObrasGov')}${card('Documentos',docs.length,'Transferegov')}${card('Propostas',props.length,'Referência complementar')}</div><div class="tabs-inline"><button data-action="municipality-tab" data-value="contratos">Contratos/convênios</button><button data-action="municipality-tab" data-value="obras">Obras</button><button data-action="municipality-tab" data-value="documentos">Documentos</button><button data-action="municipality-tab" data-value="propostas">Propostas</button></div><div id="municipalityTab"></div><div class="provenance-box"><strong>Fonte cadastral</strong><p>${esc(S.portfolio?.manifest?.source_file||'source-data/Planilha 121 municipios.xlsx')}</p></div>`;showMunicipalityTab('contratos')}
function showMunicipalityTab(t){const m=S.selectedMunicipality;if(!m)return;const contracts=municipalityContracts(m);if(t==='contratos'){const rows=contracts;$('#municipalityTab').innerHTML=rows.length?`<div class="cards">${rows.map(c=>{const i=S.contracts.indexOf(c);return `<article><span class="eyebrow">Contrato/convênio · PNCP</span><h3>${esc(contractTitle(c))}</h3><p>${esc(clipText(contractObject(c),240))}</p><small>${esc(contractMunicipality(c))} · Valor: ${moneyBR(c.valor_global||c.valorInicial||c.valor_total)}</small><button data-action="open-contract" data-value="${i}">Abrir dossiê do contrato</button></article>`}).join('')}</div>`:empty('Nenhum contrato/convênio encontrado','A fonte oficial não retornou contrato para este município.');return}if(t==='obras'){const rows=(S.integrated?.engineering||[]).filter(p=>(p.municipalities||[]).some(x=>String(x.ibge_code)===String(m.ibge_code)));$('#municipalityTab').innerHTML=rows.length?`<div class="cards">${rows.map(p=>`<article><span class="eyebrow">ObrasGov · ${esc(p.project_id)}</span><h3>${esc(p.name)}</h3><p>${esc(clipText(p.description,240))}</p><small>Situação: ${esc(p.situation)} · Execução física: ${p.physical_execution_count||0} · Contratos: ${p.contract_count||0}</small></article>`).join('')}</div>`:empty('Nenhuma obra oficial vinculada');return}if(t==='documentos'){const rows=municipalityDocuments(m);$('#municipalityTab').innerHTML=rows.length?`<div class="cards">${rows.map(d=>`<article><span class="eyebrow">Documento hábil ${esc(d.document_id)}</span><h3>${esc(d.number||'Não informado pela fonte')}</h3><p>${esc(clipText(d.observation,180))}</p><a href="${esc(d.source_url)}" target="_blank" rel="noopener noreferrer">Abrir fonte oficial</a></article>`).join('')}</div>`:empty('Nenhum documento municipal com IBGE explícito','Consulte o Centro de documentos para buscar por contrato ou identificador.');return}const rows=(S.proposals||[]).filter(p=>String(p.ibge_code)===String(m.ibge_code));$('#municipalityTab').innerHTML=rows.length?`<div class="cards">${rows.slice(0,50).map(proposalCard).join('')}</div>`:empty('Nenhuma proposta oficial encontrada')}
function engenharia(){const all=S.integrated?.engineering||[];const q=(S.engineeringQuery||'').trim().toLocaleLowerCase('pt-BR');const projects=all.filter(p=>{const text=[p.project_id,p.name,p.description,p.situation,...(p.municipalities||[]).flatMap(m=>[m.name,m.ibge_code])].filter(Boolean).join(' ').toLocaleLowerCase('pt-BR');return !q||text.includes(q)});$('#content').innerHTML=head('Obras e engenharia','Pesquise por município, código IBGE, projeto ou número de contrato de obra.')+`<div class="toolbar"><input id="engineeringSearch" value="${esc(q)}" placeholder="Município, IBGE, projeto ou contrato"><button id="engineeringSearchButton">Pesquisar</button></div><div class="metric-grid">${card('Projetos',all.length,'ObrasGov')}${card('Resultados',projects.length,'Filtro atual')}${card('Com execução física',all.filter(p=>p.physical_execution_count>0).length,'Chave oficial id_execucao_fisica')}${card('Com interrupções',all.filter(p=>p.interruption_count>0).length,'Histórico oficial')}</div><div class="cards">${projects.slice(0,200).map(p=>`<article><span class="eyebrow">ObrasGov · ${esc(p.project_id)}</span><h3>${esc(p.name||'Projeto sem nome informado')}</h3><p>${esc(clipText(p.description,260))}</p><small>Município(s): ${esc((p.municipalities||[]).map(m=>m.name).join(', ')||'Não informado pela fonte')}</small><small>Situação: ${esc(p.situation)} · Execuções: ${p.physical_execution_count||0} · Contratos: ${p.contract_count||0} · Empenhos: ${p.commitment_count||0}</small></article>`).join('')||empty('Nenhuma obra encontrada')}</div>`;const apply=()=>{S.engineeringQuery=$('#engineeringSearch').value;engenharia()};$('#engineeringSearchButton').onclick=apply;$('#engineeringSearch').onkeydown=e=>{if(e.key==='Enter')apply()}}
function documentos(){const q=(S.documentsQuery||'').trim().toLocaleLowerCase('pt-BR');const docs=S.integrated?.documents||[],orders=S.integrated?.payment_orders||[],filtered=docs.filter(d=>!q||[d.document_id,d.number,d.partnership_id,d.municipality_name,d.source_record_id].filter(Boolean).join(' ').toLocaleLowerCase('pt-BR').includes(q));$('#content').innerHTML=head('Centro de documentos e proveniência','Busque documentos por número, contrato, parceria, município ou identificador oficial.')+`<div class="toolbar"><input id="documentsSearch" value="${esc(q)}" placeholder="Número do documento, contrato, município ou parceria"><button id="documentsSearchButton">Pesquisar</button></div><div class="metric-grid">${card('Documentos hábeis',docs.length,'Transferegov')}${card('Resultados',filtered.length,'Filtro atual')}${card('Ordens de pagamento',orders.length,'Relacionadas por ID oficial')}${card('Contratos PNCP',(S.contracts||[]).length,'Proveniência disponível')}</div><div class="cards">${filtered.slice(0,200).map(d=>`<article><span class="eyebrow">Documento hábil · ${esc(d.document_id||d.source_record_id)}</span><h3>${esc(d.number||'Não informado pela fonte')}</h3><p>${esc(clipText(d.observation,220))}</p><small>Parceria: ${esc(d.partnership_id)} · Valor: ${moneyBR(d.value)} · SHA-256: ${esc(d.sha256)}</small>${d.source_url?`<a href="${esc(d.source_url)}" target="_blank" rel="noopener noreferrer">Abrir fonte oficial</a>`:''}</article>`).join('')||empty('Nenhum documento encontrado','Tente o número do contrato, município ou identificador oficial.')}</div>`;const apply=()=>{S.documentsQuery=$('#documentsSearch').value;documentos()};$('#documentsSearchButton').onclick=apply;$('#documentsSearch').onkeydown=e=>{if(e.key==='Enter')apply()}}
function timeline(){const q=(S.timelineQuery||'').trim().toLocaleLowerCase('pt-BR'),all=S.integrated?.timeline||[],rows=all.filter(r=>!q||[r.occurred_at,r.event_type,r.title,r.municipality_name,r.entity_id].filter(Boolean).join(' ').toLocaleLowerCase('pt-BR').includes(q));$('#content').innerHTML=head('Timeline integrada','Eventos oficiais pesquisáveis por contrato, município, data ou identificador.')+`<div class="toolbar"><input id="timelineSearch" value="${esc(q)}" placeholder="Contrato, município, evento ou data"><button id="timelineSearchButton">Pesquisar</button></div><div class="portfolio-meta"><span>${rows.length} evento(s) encontrado(s)</span><span>${all.length} eventos oficiais carregados</span></div><div class="cards">${rows.slice(0,300).map(r=>`<article><span class="eyebrow">${esc(r.occurred_at)} · ${esc(r.event_type)}</span><h3>${esc(r.title)}</h3><p>${esc(r.municipality_name||'Não informado pela fonte')}</p><small>${esc(r.entity)} · ${esc(r.entity_id)}</small>${r.source_url&&r.source_url!=='Não informado pela fonte'?`<a href="${esc(r.source_url)}" target="_blank" rel="noopener noreferrer">Abrir fonte oficial</a>`:''}</article>`).join('')||empty('Nenhum evento encontrado','Tente o número do contrato, município ou tipo de evento.')}</div>`;const apply=()=>{S.timelineQuery=$('#timelineSearch').value;timeline()};$('#timelineSearchButton').onclick=apply;$('#timelineSearch').onkeydown=e=>{if(e.key==='Enter')apply()}}
function municipios(){const all=filteredMunicipalities(),pages=Math.max(1,Math.ceil(all.length/S.pageSize));S.municipalityPage=Math.max(1,Math.min(S.municipalityPage,pages));const start=(S.municipalityPage-1)*S.pageSize,rows=all.slice(start,start+S.pageSize);$('#content').innerHTML=head('Carteira de municípios','121 municípios oficiais da carteira, com mapa do Paraná baseado nas malhas municipais do IBGE.')+`<div class="toolbar"><input id="munSearch" value="${esc(S.municipalityQuery)}" placeholder="Pesquisar município, CNPJ ou código IBGE"><button data-action="municipality-search">Pesquisar</button></div><div class="map-panel"><div class="map-heading"><h2>Mapa da carteira no Paraná</h2><small>Fonte: malha municipal oficial IBGE · pontos = centroides geométricos dos limites oficiais</small></div><div id="ibgeMap" class="ibge-map"><p>Carregando malha oficial do IBGE…</p></div></div><div class="portfolio-meta"><span>${all.length} resultado(s)</span><span>Fonte cadastral: ${esc(S.portfolio.manifest.source_file)}</span><span>Mapa: IBGE, carregamento oficial</span></div><div class="municipality-grid">${rows.map(m=>`<button class="municipality-card" data-action="open-municipality" data-value="${esc(m.ibge_code)}"><span class="initial">${esc(m.name.slice(0,2).toUpperCase())}</span><div><strong>${esc(m.name)}</strong><small>IBGE ${esc(m.ibge_code)}</small><small>CNPJ ${esc(m.cnpj)}</small></div><b>→</b></button>`).join('')}</div><div class="pager"><button ${S.municipalityPage===1?'disabled':''} data-action="municipality-page" data-value="-1">Anterior</button><span>Página ${S.municipalityPage} de ${pages}</span><button ${S.municipalityPage===pages?'disabled':''} data-action="municipality-page" data-value="1">Próxima</button></div>`;$('#munSearch').addEventListener('keydown',e=>{if(e.key==='Enter')applyMunicipalitySearch()});renderIbgeMap()}
function geoPoints(coords,out=[]){if(!Array.isArray(coords))return out;if(typeof coords[0]==='number'){out.push(coords);return out}coords.forEach(item=>geoPoints(item,out));return out}
function renderIbgeMap(){const box=$('#ibgeMap');if(!box)return;fetch('https://servicodados.ibge.gov.br/api/v3/malhas/estados/41?formato=application/vnd.geo+json&qualidade=minima&intrarregiao=municipio').then(r=>{if(!r.ok)throw new Error('IBGE HTTP '+r.status);return r.json()}).then(gj=>{const allowed=new Map((S.portfolio?.municipalities||[]).map(m=>[String(m.ibge_code),m]));const features=(gj.features||[]).filter(f=>allowed.has(String(f.properties?.codarea||f.properties?.codigo||f.id||'')));const points=features.map(f=>{const p=geoPoints(f.geometry?.coordinates,[]);const lon=p.reduce((s,x)=>s+x[0],0)/p.length,lat=p.reduce((s,x)=>s+x[1],0)/p.length;return {lon,lat,m:allowed.get(String(f.properties?.codarea||f.properties?.codigo||f.id||''))}}).filter(x=>Number.isFinite(x.lon)&&Number.isFinite(x.lat));if(!points.length)throw new Error('Nenhum município da carteira na malha retornada');const minLon=Math.min(...points.map(p=>p.lon)),maxLon=Math.max(...points.map(p=>p.lon)),minLat=Math.min(...points.map(p=>p.lat)),maxLat=Math.max(...points.map(p=>p.lat)),sx=x=>20+(x-minLon)/(maxLon-minLon||1)*760,sy=y=>20+(maxLat-y)/(maxLat-minLat||1)*440;box.innerHTML=`<svg viewBox="0 0 800 480" role="img" aria-label="Municípios da carteira no Paraná">${points.map(p=>`<g class="map-point" tabindex="0" data-action="open-municipality" data-value="${esc(p.m.ibge_code)}"><circle cx="${sx(p.lon).toFixed(1)}" cy="${sy(p.lat).toFixed(1)}" r="4"></circle><title>${esc(p.m.name)} · IBGE ${esc(p.m.ibge_code)}</title></g>`).join('')}</svg><small>${points.length} ponto(s) da carteira encontrados na malha oficial. O ponto representa o centroide geométrico do limite municipal.</small>`}).catch(err=>{console.warn('Falha ao carregar malha IBGE',err);box.innerHTML='<p>Não foi possível carregar a malha oficial do IBGE agora. A lista de municípios permanece disponível.</p>'})}
function exportCurrent(){const sets={municipios:S.portfolio?.municipalities||[],instrumentos:S.contracts||[],dossie:S.contracts||[],engenharia:S.integrated?.engineering||[],documentos:S.integrated?.documents||[],timeline:S.integrated?.timeline||[],financeiro:S.integrated?.accounts||[],riscos:S.integrated?.risks||[]};const rows=sets[S.view]||S.contracts||[];if(!rows.length)return;const keys=[...new Set(rows.flatMap(row=>Object.keys(row)))];const csv=[keys.join(';'),...rows.map(row=>keys.map(key=>`"${String(row[key]??'').replace(/"/g,'""')}"`).join(';'))].join('\n');const blob=new Blob(["\ufeff"+csv],{type:'text/csv;charset=utf-8'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=`govparcerias-${S.view||'dados'}-${APP_VERSION}.csv`;a.click();URL.revokeObjectURL(url)}
// Timeline unificada: inclui eventos PNCP/Transferegov já normalizados e as
// movimentações do download oficial, permitindo pesquisa por convênio/contrato.
timeline=function(){const q=(S.timelineQuery||'').trim().toLocaleLowerCase('pt-BR'),base=S.integrated?.timeline||[],d=S.discretionary||{},extra=[...(d.contracts||[]).map(r=>({occurred_at:r.DATA_ASSINATURA_CONTRATO||r.DATA_PUBLICACAO_CONTRATO,event_type:'transferegov_contract',title:`Contrato ${r.NR_CONTRATO||r.ID_CONTRATO||'Não informado pela fonte'}`,entity:'siconv_contrato',entity_id:r.ID_CONTRATO||r.ID_LICITACAO,source_url:'https://api-publica.transferegov.gestao.gov.br/downloads'})),...(d.payments||[]).map(r=>({occurred_at:r.DATA_PAG,event_type:'transferegov_payment',title:`Pagamento ${r.NR_MOV_FIN||'Não informado pela fonte'}`,entity:'siconv_pagamento',entity_id:r.NR_MOV_FIN,detail:`Convênio ${r.NR_CONVENIO||'Não informado pela fonte'}`,source_url:'https://api-publica.transferegov.gestao.gov.br/downloads'}))];const all=[...base,...extra],rows=all.filter(r=>!q||[r.occurred_at,r.event_type,r.title,r.municipality_name,r.entity_id,r.detail].filter(Boolean).join(' ').toLocaleLowerCase('pt-BR').includes(q));$('#content').innerHTML=head('Timeline integrada','Eventos oficiais pesquisáveis por contrato, convênio, município, pagamento ou data.')+`<div class="toolbar"><input id="timelineSearch" value="${esc(q)}" placeholder="Contrato, convênio, pagamento, município ou data"><button id="timelineSearchButton">Pesquisar</button></div><div class="portfolio-meta"><span>${rows.length} evento(s) encontrado(s)</span><span>${all.length} eventos oficiais carregados</span></div><div class="cards">${rows.slice(0,300).map(r=>`<article><span class="eyebrow">${esc(r.occurred_at||'Não informado pela fonte')} · ${esc(r.event_type)}</span><h3>${esc(r.title)}</h3><p>${esc(r.municipality_name||r.detail||'Não informado pela fonte')}</p><small>${esc(r.entity||'fonte oficial')} · ${esc(r.entity_id||'Não informado pela fonte')}</small>${r.source_url?`<a href="${esc(r.source_url)}" target="_blank" rel="noopener noreferrer">Abrir fonte oficial</a>`:''}</article>`).join('')||empty('Nenhum evento encontrado','Tente contrato, convênio, pagamento ou município.')}</div>`;const apply=()=>{S.timelineQuery=$('#timelineSearch').value;timeline()};$('#timelineSearchButton').onclick=apply;$('#timelineSearch').onkeydown=e=>{if(e.key==='Enter')apply()}};
// Dossiê operacional Transferegov: contrato → licitação → convênio → execução financeira.
openTransferContract=function(id){
  const d=S.discretionary||{}, contract=(d.contracts||[]).find(row=>String(row.ID_CONTRATO)===String(id));
  if(!contract)return;
  const licitation=(d.procurements||[]).find(row=>String(row.ID_LICITACAO)===String(contract.ID_LICITACAO));
  const agreement=(d.agreements||[]).find(row=>String(row.NR_CONVENIO)===String(licitation?.NR_CONVENIO));
  const convenio=agreement?.NR_CONVENIO;
  const commitments=(d.commitments||[]).filter(row=>String(row.NR_CONVENIO)===String(convenio));
  const disbursements=(d.disbursements||[]).filter(row=>String(row.NR_CONVENIO)===String(convenio));
  const payments=(d.payments||[]).filter(row=>String(row.NR_CONVENIO)===String(convenio));
  const source='https://api-publica.transferegov.gestao.gov.br/downloads';
  $('#content').innerHTML=head(`Dossiê · contrato ${contract.NR_CONTRATO||id}`,'Visão operacional do instrumento e sua execução financeira oficial.',`<button data-action="show" data-value="instrumentos">← Voltar aos contratos</button>`)+
  `<div class="metric-grid">${card('Contrato',contract.NR_CONTRATO||'Não informado pela fonte','Transferegov')}${card('Convênio',convenio||'Não informado pela fonte','Vínculo oficial')}${card('Empenhos',commitments.length,'Registros oficiais')}${card('Desembolsos',disbursements.length,'Registros oficiais')}${card('Pagamentos',payments.length,'Registros oficiais')}</div>
  <div class="section-grid"><article class="panel"><span class="eyebrow">Identificação e vínculo</span><div class="field-grid">${field('ID do contrato',contract.ID_CONTRATO)}${field('Número',contract.NR_CONTRATO)}${field('Licitação',contract.ID_LICITACAO)}${field('Convênio',convenio)}${field('Fornecedor',contract.NOME_FORNECEDOR_CONTRATO)}${field('Objeto',contract.OBJETO_CONTRATO)}${field('Valor global',moneyBR(contract.VALOR_GLOBAL_CONTRATO))}${field('Vigência',`${contract.DATA_INICIO_VIGENCIA_CONTRATO||'Não informado pela fonte'} a ${contract.DATA_FIM_VIGENCIA_CONTRATO||'Não informado pela fonte'}`)}</div><a href="${source}" target="_blank" rel="noopener noreferrer">Abrir fonte oficial Transferegov</a></article><article class="panel"><span class="eyebrow">Situação do convênio</span><div class="field-grid">${field('Situação',agreement?.SIT_CONVENIO)}${field('Processo',agreement?.NR_PROCESSO)}${field('Valor global',moneyBR(agreement?.VL_GLOBAL_CONV))}${field('Valor repassado',moneyBR(agreement?.VL_REPASSE_CONV))}${field('Valor empenhado',moneyBR(agreement?.VL_EMPENHADO_CONV))}${field('Valor desembolsado',moneyBR(agreement?.VL_DESEMBOLSADO_CONV))}</div></article></div>
  <h2>Pagamentos</h2>${payments.length?`<div class="table-wrap"><table><thead><tr><th>Data</th><th>Fornecedor</th><th>Documento</th><th>Valor</th></tr></thead><tbody>${payments.slice(0,200).map(row=>`<tr><td>${esc(row.DATA_PAG||'Não informado pela fonte')}</td><td>${esc(row.NOME_FORNECEDOR||'Não informado pela fonte')}</td><td>${esc(row.NR_DL||row.NR_MOV_FIN||'Não informado pela fonte')}</td><td>${moneyBR(row.VL_PAGO)}</td></tr>`).join('')}</tbody></table></div>`:empty('Nenhum pagamento relacionado pela fonte')}
  <h2>Empenhos e desembolsos</h2><div class="cards">${[...commitments.slice(0,30).map(row=>`<article><span class="eyebrow">Empenho · ${esc(row.NR_EMPENHO)}</span><h3>${moneyBR(row.VALOR_EMPENHO)}</h3><p>${esc(row.DESC_SITUACAO_EMPENHO||'Não informado pela fonte')}</p><small>${esc(row.DATA_EMISSAO||'Não informado pela fonte')}</small></article>`),...disbursements.slice(0,30).map(row=>`<article><span class="eyebrow">Desembolso · ${esc(row.ID_DESEMBOLSO)}</span><h3>${moneyBR(row.VL_DESEMBOLSADO)}</h3><p>${esc(row.DATA_DESEMBOLSO||'Não informado pela fonte')}</p><small>${esc(row.OBSERVACAO_DH||'Não informado pela fonte')}</small></article>`)].join('')||empty('Nenhum empenho ou desembolso relacionado')}</div>`;
};
Object.assign(window,{S});boot();
