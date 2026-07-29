const S={data:null,contract:null,portfolio:null,contracts:[],proposals:[],view:'inicio',homeQuery:'',theme:localStorage.getItem('gpa:theme')||'dark',selectedSection:'identificacao',selectedMunicipality:null,selectedOfficialProposal:null,municipalityQuery:'',municipalityPage:1,pageSize:18};
const $=q=>document.querySelector(q); const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
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
  [S.data,S.contract,S.portfolio,S.contracts,S.proposals]=await Promise.all([
    safeJson('data/demo.json',{}),
    safeJson('data/dossier-contract.json',{sections:[]}),
    safeJson('data/municipalities.json',{manifest:{record_count:0},municipalities:[]}),
    safeJson('data/contracts.json',[]),
    safeJson('data/proposals.json',[])
  ]);
  if(!Array.isArray(S.contracts))S.contracts=S.contracts.items||S.contracts.contracts||S.contracts.data||[];
  if(!Array.isArray(S.proposals))S.proposals=S.proposals.items||S.proposals.proposals||S.proposals.data||[];
  document.documentElement.dataset.theme=S.theme;
  renderShell();
  show('inicio')
}
const nav=[['inicio','Visão integrada'],['municipios','Municípios'],['territorial','Gestão territorial'],['instrumentos','Contratos e propostas'],['dossie','Dossiê por contrato'],['financeiro','Inteligência financeira'],['engenharia','Obras e engenharia'],['documentos','Centro de documentos'],['timeline','Timeline integrada'],['riscos','Risco e conformidade'],['copiloto','Copiloto']];
function renderShell(){$('#app').innerHTML=`<div class="layout"><aside class="sidebar"><div class="brand"><div class="logo">GP</div><div><strong>GovParcerias</strong><small>Intelligence</small></div></div><nav>${nav.map(([id,t])=>`<button data-view="${id}">${t}</button>`).join('')}</nav><div class="policy">Integridade official-only<br><small>Carteira administrativa separada da base pública oficial.</small></div></aside><main><header class="topbar"><div><strong>Operação por contrato · gestão por território</strong><small> Uma base, duas jornadas complementares</small></div><div><button id="cmd">Ctrl K</button><button id="theme">${S.theme==='dark'?'Claro':'Escuro'}</button><span class="badge">v1.1.0-alpha</span></div></header><section id="content"></section><footer>121 municípios · ${(S.proposals||[]).length} propostas Transferegov · ${(S.contracts||[]).length} contratos PNCP · official-only</footer></main></div><aside id="chat" class="chat"><header><div><strong>Copiloto verificável</strong><small>Território, município e contrato</small></div><button onclick="closeChat()">×</button></header><div class="chat-body"><div class="notice"><strong>Política ativa.</strong> A carteira identifica o universo de trabalho. Respostas sobre contratos, propostas, valores, obras e documentos exigem evidência pública oficial.</div></div><div class="chat-input"><input placeholder="Pergunte por município, proposta ou contrato"><button onclick="assistantBlocked()">Enviar</button></div></aside><div id="palette" class="palette"><div class="palette-box"><input id="paletteInput" placeholder="Digite uma página ou comando"><div>${nav.map(([id,t])=>`<button onclick="closePalette();show('${id}')">${t}</button>`).join('')}</div></div></div>`;document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>show(b.dataset.view));$('#theme').onclick=toggleTheme;$('#cmd').onclick=openPalette;document.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'){e.preventDefault();openPalette()}if(e.key==='Escape'){closePalette();closeChat()}})}
function toggleTheme(){S.theme=S.theme==='dark'?'light':'dark';document.documentElement.dataset.theme=S.theme;localStorage.setItem('gpa:theme',S.theme);renderShell();show(S.view)}
function show(v){S.view=v;document.querySelectorAll('[data-view]').forEach(b=>b.classList.toggle('active',b.dataset.view===v));({inicio,municipios,territorial,instrumentos,dossie,financeiro,engenharia,documentos,timeline,riscos,copiloto}[v]||inicio)()}
const head=(t,p,a='')=>`<div class="hero"><div><h1>${t}</h1><p>${p}</p></div>${a}</div>`;
const empty=(title='Nenhum dado oficial sincronizado',detail='A estrutura está pronta e não será preenchida por estimativas ou demonstrações fictícias.')=>`<div class="empty"><div class="empty-icon">✓</div><h2>${title}</h2><p>${detail}</p></div>`;
const card=(label,value,detail='')=>`<article class="metric"><span>${label}</span><strong>${value}</strong><small>${detail}</small></article>`;
function inicio(){
  const m=S.portfolio?.manifest||{};
  const totalContracts=Array.isArray(S.contracts)?S.contracts.length:0;
  const totalProposals=Array.isArray(S.proposals)?S.proposals.length:0;
  $('#content').innerHTML=
    head('Consulta unificada','Pesquise em um único campo por município, CNPJ, código IBGE, proposta, contrato, processo, objeto, fornecedor ou órgão.')
    +`<div class="home-search-grid">
      <article class="home-search-card">
        <span class="eyebrow">Busca integrada</span>
        <h2>Consultar propostas, contratos e municípios</h2>
        <p>A pesquisa combina a carteira dos 121 municípios com propostas Transferegov e contratos PNCP.</p>
        <div class="home-search">
          <input id="unifiedHomeSearch" value="${esc(S.homeQuery||'')}" placeholder="Ex.: Altamira, 100, CNPJ, processo, objeto ou fornecedor">
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
      ${card('Integridade','Official-only','Sem valores ou registros inventados')}
    </div>
    <div class="truth-banner"><strong>Separação de confiança</strong><span>Municípios da carteira, propostas e contratos oficiais permanecem identificados por sua proveniência.</span></div>`;

  $('#unifiedSearchButton').onclick=searchUnifiedHome;
  $('#unifiedHomeSearch').addEventListener('keydown',e=>{if(e.key==='Enter')searchUnifiedHome()});
  $('#aiHomeButton').onclick=askHomeAI;
  $('#aiHomeInput').addEventListener('keydown',e=>{if(e.key==='Enter')askHomeAI()})
}
function searchMunicipalityHome(){S.homeQuery=$('#municipalityHomeSearch')?.value?.trim()||'';show('instrumentos')}
function searchContractHome(){S.homeQuery=$('#contractHomeSearch')?.value?.trim()||'';show('instrumentos')}
function searchUnifiedHome(){
  S.homeQuery=($('#unifiedHomeSearch')?.value||'').trim();
  show('instrumentos')
}
function askHomeAI(){
  const input=$('#aiHomeInput');
  const q=(input?.value||'').trim();
  if(!q)return;
  const box=$('#aiConversation');
  const terms=normalizeSearch(q).split(/\s+/).filter(x=>x.length>2&&!['mostre','quais','existe','contrato','contratos','municipio','municipios','sobre','para','com','numero'].includes(x));
  const contracts=(S.contracts||[]).filter(c=>terms.every(t=>contractHaystack(c).includes(t)));
  const proposals=(S.proposals||[]).filter(p=>terms.every(t=>proposalHaystack(p).includes(t)));
  const municipalities=(S.portfolio?.municipalities||[]).filter(m=>terms.every(t=>municipalityHaystack(m).includes(t)));
  box.innerHTML+=`<div class="notice"><strong>Você:</strong> ${esc(q)}</div>`;
  if(contracts.length||proposals.length||municipalities.length){
    const searchTerm=terms.join(' ')||q;
    box.innerHTML+=`<div class="notice"><strong>GovParcerias AI:</strong> Encontrei ${proposals.length} proposta(s), ${contracts.length} contrato(s) e ${municipalities.length} município(s) relacionados. <button id="aiViewResults">Ver resultados</button></div>`;
    const resultButton=$('#aiViewResults');
    if(resultButton)resultButton.onclick=()=>{S.homeQuery=searchTerm;show('instrumentos')}
  }else{
    box.innerHTML+=`<div class="notice"><strong>GovParcerias AI:</strong> Não encontrei evidências correspondentes na base atualmente sincronizada.</div>`
  }
  input.value='';
  box.scrollTop=box.scrollHeight
}

function filteredMunicipalities(){const q=S.municipalityQuery.trim().toLocaleLowerCase('pt-BR');return S.portfolio.municipalities.filter(m=>!q||[m.name,m.cnpj,m.ibge_code].some(x=>x.toLocaleLowerCase('pt-BR').includes(q)))}
function municipios(){const all=filteredMunicipalities(),pages=Math.max(1,Math.ceil(all.length/S.pageSize));S.municipalityPage=Math.min(S.municipalityPage,pages);const start=(S.municipalityPage-1)*S.pageSize,rows=all.slice(start,start+S.pageSize);$('#content').innerHTML=head('Carteira de municípios','121 municípios cadastrados a partir da planilha fornecida, com CNPJ e código IBGE preservados exatamente como recebidos.')+`<div class="toolbar"><input id="munSearch" value="${esc(S.municipalityQuery)}" placeholder="Pesquisar município, CNPJ ou código IBGE"><button onclick="applyMunicipalitySearch()">Pesquisar</button></div><div class="portfolio-meta"><span>${all.length} resultado(s)</span><span>Fonte: ${esc(S.portfolio.manifest.source_file)}</span><span>Validação: sem duplicidades</span></div><div class="municipality-grid">${rows.map(m=>`<button class="municipality-card" onclick="openMunicipality('${m.ibge_code}')"><span class="initial">${esc(m.name.slice(0,2).toUpperCase())}</span><div><strong>${esc(m.name)}</strong><small>IBGE ${m.ibge_code}</small><small>CNPJ ${m.cnpj}</small></div><b>→</b></button>`).join('')}</div><div class="pager"><button ${S.municipalityPage===1?'disabled':''} onclick="changeMunicipalityPage(-1)">Anterior</button><span>Página ${S.municipalityPage} de ${pages}</span><button ${S.municipalityPage===pages?'disabled':''} onclick="changeMunicipalityPage(1)">Próxima</button></div>`;$('#munSearch').addEventListener('keydown',e=>{if(e.key==='Enter')applyMunicipalitySearch()})}
function applyMunicipalitySearch(){S.municipalityQuery=$('#munSearch').value;S.municipalityPage=1;municipios()} function changeMunicipalityPage(d){S.municipalityPage+=d;municipios()}
function openMunicipality(code){S.selectedMunicipality=S.portfolio.municipalities.find(m=>m.ibge_code===code);municipalityProfile()}
function municipalityProfile(){
  const m=S.selectedMunicipality;
  if(!m)return show('municipios');
  const proposals=(S.proposals||[]).filter(p=>String(p.ibge_code)===String(m.ibge_code));
  const contracts=(S.contracts||[]).filter(c=>String(c.ibge_code||'')===String(m.ibge_code));
  $('#content').innerHTML=head(m.name,'Visão municipal com propostas Transferegov e contratos PNCP oficialmente sincronizados.',`<button onclick="show('municipios')">← Voltar à carteira</button>`)
    +`<div class="profile-head"><div class="profile-mark">${esc(m.name.slice(0,2).toUpperCase())}</div><div><span class="eyebrow">Município da carteira</span><h2>${esc(m.name)}</h2><p>CNPJ ${esc(m.cnpj)} · Código IBGE ${esc(m.ibge_code)}</p></div><span class="source-pill">Carteira de trabalho</span></div>
      <div class="metric-grid">${card('Propostas oficiais',proposals.length,'Transferegov')}${card('Contratos oficiais',contracts.length,'PNCP')}${card('Obras oficiais','—','Fonte ainda não sincronizada')}${card('Alertas verificáveis','—','Motor aguarda evidências')}</div>
      <div class="tabs-inline"><button onclick="showMunicipalityTab('propostas')">Propostas</button><button onclick="showMunicipalityTab('contratos')">Contratos</button><button onclick="showMunicipalityTab('obras')">Obras</button><button onclick="showMunicipalityTab('documentos')">Documentos</button></div>
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
      ?`<div class="cards">${rows.map(c=>{const idx=(S.contracts||[]).indexOf(c);return `<article><span class="eyebrow">Contrato oficial · PNCP</span><h3>${esc(contractTitle(c))}</h3><p>${esc(contractObject(c))}</p><button onclick="openContractResult(${idx})">Abrir contrato</button></article>`}).join('')}</div>`
      :empty('Nenhum contrato oficial vinculado','Nenhum contrato PNCP da base atual possui este código IBGE.');
    return
  }
  const names={obras:'obra',documentos:'documento'};
  $('#municipalityTab').innerHTML=empty(`Nenhum ${names[t]} oficial vinculado`,'A plataforma não criará registros sintéticos para preencher esta área.')
}
function territorial(){$('#content').innerHTML=head('Gestão territorial e municipal','Visão macro para gerência sem perder a rastreabilidade até o contrato de origem.')+`<div class="metric-grid">${card('Carteira atual','121 municípios','Recorte administrativo')}${card('Regiões oficiais','—','Aguardando fonte territorial')}${card('Contratos consolidados','—','Aguardando sincronização')}${card('Recursos consolidados','—','Nenhum total sem fonte')}</div><div class="cards"><article><h3>Carteira completa</h3><p>Consolidação dos 121 municípios cadastrados, com filtros e acesso ao perfil individual.</p><button onclick="show('municipios')">Explorar municípios</button></article><article><h3>Comparação municipal</h3><p>Comparações financeiras, físicas e de risco serão habilitadas somente após a coleta oficial.</p><button disabled>Sem dados oficiais</button></article><article><h3>Recortes territoriais</h3><p>Regiões imediatas, intermediárias e outros agrupamentos serão obtidos de fonte pública oficial.</p><button disabled>Aguardando conector</button></article></div>${empty('Indicadores territoriais ainda indisponíveis','O único agregado liberado nesta versão é a contagem dos 121 registros da carteira fornecida.')}`}
function contractResults(){const q=(S.homeQuery||'').trim().toLocaleLowerCase('pt-BR');return (S.contracts||[]).filter(c=>!q||JSON.stringify(c).toLocaleLowerCase('pt-BR').includes(q))}
function normalizeSearch(v){return String(v??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('pt-BR')}
function moneyBR(v){if(v===null||v===undefined||v==='')return 'Não informado pela fonte';const n=Number(v);return Number.isFinite(n)?n.toLocaleString('pt-BR',{style:'currency',currency:'BRL'}):esc(v)}
function contractHaystack(c){return normalizeSearch(JSON.stringify(c))}
function municipalityHaystack(m){return normalizeSearch([m.name,m.cnpj,m.ibge_code].join(' '))}
function contractTitle(c){return c.numero||c.number||c.numeroContratoEmpenho||c.source_record_id||'Não informado pela fonte'}
function contractMunicipality(c){return c.municipality_name||c.municipioNome||c.orgao_nome||c.orgaoEntidade?.razaoSocial||'Não informado pela fonte'}
function contractObject(c){return c.objeto||c.objetoContrato||c.object||'Não informado pela fonte'}

function normalizeSearch(v){
  return String(v??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('pt-BR').replace(/[./\-]/g,' ').replace(/\s+/g,' ').trim()
}
function digitsOnly(v){return String(v??'').replace(/\D/g,'')}
function moneyBR(v){
  if(v===null||v===undefined||v==='')return 'Não informado pela fonte';
  const n=Number(v);
  return Number.isFinite(n)?n.toLocaleString('pt-BR',{style:'currency',currency:'BRL'}):esc(v)
}
function contractHaystack(c){
  const raw=[c.source_record_id,c.numero,c.number,c.numeroContratoEmpenho,c.ano,c.processo,c.objeto,c.objetoContrato,c.municipality_name,c.municipioNome,c.municipality_cnpj,c.orgao_cnpj,c.orgao_nome,c.fornecedor_nome,c.fornecedor_documento,c.nomeRazaoSocialFornecedor,c.niFornecedor,c.numeroControlePNCP,c.orgaoEntidade?.cnpj,c.orgaoEntidade?.razaoSocial,c.unidadeOrgao?.nomeUnidade].filter(Boolean).join(' ');
  return normalizeSearch(raw)+' '+digitsOnly(raw)
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
function queryMatches(haystack,q){
  const normalized=normalizeSearch(q);
  const digits=digitsOnly(q);
  if(!normalized&&!digits)return true;
  const tokens=normalized.split(' ').filter(Boolean);
  return tokens.every(t=>haystack.includes(t))||(digits&&haystack.includes(digits))
}
function contractTitle(c){return c.numero||c.number||c.numeroContratoEmpenho||c.source_record_id||'Não informado pela fonte'}
function contractMunicipality(c){return c.municipality_name||c.municipioNome||c.orgao_nome||c.orgaoEntidade?.razaoSocial||'Não informado pela fonte'}
function contractObject(c){return c.objeto||c.objetoContrato||c.object||'Não informado pela fonte'}

function instrumentos(){
  const query=S.homeQuery||'';
  const contracts=(S.contracts||[]).filter(c=>queryMatches(contractHaystack(c),query));
  const proposals=(S.proposals||[]).filter(p=>queryMatches(proposalHaystack(p),query));
  const municipalities=(S.portfolio?.municipalities||[]).filter(m=>queryMatches(municipalityHaystack(m),query));

  const contractCards=contracts.slice(0,100).map(c=>{
    const idx=(S.contracts||[]).indexOf(c);
    return `<article>
      <span class="eyebrow">Contrato oficial · ${esc(c.source||'PNCP')}</span>
      <h3>Contrato ${esc(contractTitle(c))}</h3>
      <p><strong>${esc(contractMunicipality(c))}</strong></p>
      <p>${esc(contractObject(c))}</p>
      <small>Processo: ${esc(c.processo||c.numeroProcesso||'Não informado pela fonte')} · Valor: ${moneyBR(c.valor_global??c.valorGlobal??c.valorInicial)}</small>
      <button onclick="openContractResult(${idx})">Abrir contrato</button>
    </article>`
  }).join('');

  const proposalCards=proposals.slice(0,50).map(p=>proposalCard(p)).join('');

  const municipalityCards=municipalities.slice(0,50).map(m=>`
    <article>
      <span class="eyebrow">Município da carteira</span>
      <h3>${esc(m.name)}</h3>
      <p>CNPJ ${esc(m.cnpj)} · IBGE ${esc(m.ibge_code)}</p>
      <button onclick="openMunicipalityFromSearch('${esc(m.ibge_code)}')">Abrir município</button>
    </article>`).join('');

  const summary=query
    ?`${proposals.length} proposta(s), ${contracts.length} contrato(s) e ${municipalities.length} município(s) encontrado(s) para “${esc(query)}”.`
    :`${proposals.length} proposta(s), ${contracts.length} contrato(s) e ${municipalities.length} município(s) disponíveis.`;

  $('#content').innerHTML=
    head('Consulta unificada','Pesquise por município, CNPJ, IBGE, proposta, contrato, processo, objeto, fornecedor ou órgão.',`<button id="backToHomeButton">← Voltar</button>`)
    +`<div class="toolbar">
       <input id="contractSearch" value="${esc(query)}" placeholder="Digite qualquer termo da consulta">
       <button id="contractSearchButton">Pesquisar</button>
      </div>
      <div class="portfolio-meta"><span>${summary}</span><span>Propostas: ${(S.proposals||[]).length}</span><span>Contratos: ${(S.contracts||[]).length}</span><span>Modo: official-only</span></div>
      ${proposals.length?`<h2>Propostas oficiais</h2><div class="cards">${proposalCards}</div>`:''}
      ${contracts.length?`<h2>Contratos oficiais</h2><div class="cards">${contractCards}</div>`:''}
      ${municipalities.length?`<h2>Municípios</h2><div class="cards">${municipalityCards}</div>`:''}
      ${!proposals.length&&!contracts.length&&!municipalities.length?empty('Nenhum resultado localizado',`A consulta por ${esc(query)} não encontrou propostas, contratos nem municípios.`):''}`;

  $('#contractSearchButton').onclick=applyContractSearch;
  const backToHomeButton=$('#backToHomeButton');
  if(backToHomeButton)backToHomeButton.onclick=()=>show('inicio');
  $('#contractSearch').addEventListener('keydown',e=>{if(e.key==='Enter')applyContractSearch()});
  const backButton=$('#backToHomeButton');
  if(backButton)backButton.onclick=()=>show('inicio')
}
function applyContractSearch(){S.homeQuery=($('#contractSearch')?.value||'').trim();instrumentos()}
function openMunicipalityFromSearch(code){
  S.selectedMunicipality=(S.portfolio?.municipalities||[]).find(m=>String(m.ibge_code)===String(code));
  municipalityProfile()
}
function openContractResult(index){S.selectedOfficialContract=(S.contracts||[])[index];contractDetail()}
function proposalCard(p){
  const idx=(S.proposals||[]).indexOf(p);
  return `<article>
    <span class="eyebrow">Proposta oficial · Transferegov</span>
    <h3>Proposta ${esc(p.id_proposta||p.source_record_id)}</h3>
    <p><strong>${esc(p.municipality_name)}</strong> · ${esc(p.receiver_name)}</p>
    <p>${esc(clipText(p.object))}</p>
    <small>Situação: ${esc(p.status)} · Valor: ${moneyBR(p.total_value)}</small>
    <button onclick="openProposalResult(${idx})">Abrir proposta</button>
  </article>`
}
function openProposalResult(index){S.selectedOfficialProposal=(S.proposals||[])[index];proposalDetail()}
function proposalDetail(){
  const p=S.selectedOfficialProposal;
  if(!p)return show('instrumentos');
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
    head(`Proposta ${esc(p.id_proposta)}`,'Registro oficial do Transferegov com proveniência verificável.',`<button onclick="show('instrumentos')">← Voltar aos resultados</button>`)
    +`<div class="section-head"><div><span class="eyebrow">Proposta oficial</span><h2>${esc(p.municipality_name)}</h2><p>${esc(p.object)}</p></div><span class="source-pill">Transferegov</span></div>
      <div class="field-grid">${fields.map(([label,value])=>`<div class="field"><label>${esc(label)}</label><strong>${label.includes('Valor')?value:esc(value||'Não informado pela fonte')}</strong></div>`).join('')}</div>`
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
    head(`Contrato ${esc(contractTitle(c))}`,'Registro oficial sincronizado e apresentado com sua proveniência.',`<button onclick="show('instrumentos')">← Voltar aos resultados</button>`)
    +`<div class="section-head"><div><span class="eyebrow">Contrato oficial</span><h2>${esc(contractMunicipality(c))}</h2><p>${esc(contractObject(c))}</p></div><span class="source-pill">${esc(c.source||'PNCP')}</span></div>
      <div class="field-grid">${fields.map(([label,value])=>`<div class="field"><label>${esc(label)}</label><strong>${label.includes('Valor')?value:esc(value)}</strong></div>`).join('')}</div>`
}

function dossie(){$('#content').innerHTML=head('Dossiê integral por contrato','Núcleo operacional para analistas, engenheiros, arquitetos, fiscais e equipes financeiras.')+`<div class="dossier"><aside class="tabs">${S.contract.sections.map(s=>`<button class="${S.selectedSection===s.id?'active':''}" onclick="selectSection('${s.id}')">${s.title}</button>`).join('')}</aside><section class="dossier-main">${sectionView()}</section></div>`}
function selectSection(id){S.selectedSection=id;dossie()} function sectionView(){const s=S.contract.sections.find(x=>x.id===S.selectedSection);return `<div class="section-head"><div><span class="eyebrow">Contrato não selecionado</span><h2>${s.title}</h2><p>Campos previstos. O preenchimento exige registro oficial validado.</p></div><span class="source-pill">Sem evidência</span></div><div class="field-grid">${s.fields.map(f=>`<div class="field"><label>${f.replaceAll('_',' ')}</label><strong>Não informado pela fonte</strong><small>Sem registro oficial sincronizado</small></div>`).join('')}</div>`}
function generic(title,desc,detail){$('#content').innerHTML=head(title,desc)+empty(detail)}
function financeiro(){generic('Inteligência financeira','Repasse, contrapartida, empenhos, pagamentos, contas, extratos e conciliação por contrato.','Nenhum registro financeiro oficial carregado')}
function engenharia(){generic('Obras e engenharia','Projetos, medições, vistorias, ART/RRT, cronogramas, fotos, aditivos e recebimentos.','Nenhuma obra ou vistoria oficial carregada')}
function documentos(){generic('Centro de documentos','Pesquisa, versionamento, comparação, hash e citações de documentos públicos.','Nenhum documento oficial indexado')}
function timeline(){generic('Timeline integrada','Eventos contratuais, financeiros, físicos, documentais e de fiscalização em sequência auditável.','Nenhum evento oficial carregado')}
function riscos(){generic('Risco e conformidade','Regras determinísticas, requisitos explícitos e evidências reproduzíveis.','Nenhum alerta calculado sem evidência')}
function copiloto(){$('#content').innerHTML=head('Copiloto territorial e contratual','O mesmo agente atende perguntas operacionais por contrato e perguntas gerenciais por município ou território.')+`<div class="ai-policy"><h2>Escopo de consulta</h2><ol><li>Contrato individual: detalhe técnico, financeiro, documental e histórico.</li><li>Município: consolidação de todos os contratos oficialmente vinculados.</li><li>Território: agregação rastreável dos municípios e contratos componentes.</li><li>Ausência de evidência: resposta explícita, sem inferência factual.</li></ol><button class="primary" onclick="openChat()">Abrir copiloto</button></div>`}
function openChat(){$('#chat').classList.add('open')} function closeChat(){$('#chat').classList.remove('open')} function openPalette(){$('#palette').classList.add('open');setTimeout(()=>$('#paletteInput')?.focus(),20)} function closePalette(){$('#palette').classList.remove('open')} function assistantBlocked(){alert('Ainda não há contratos e documentos oficiais sincronizados. O copiloto não produzirá afirmações factuais sem evidência recuperada.')}
Object.assign(window,{show,selectSection,openChat,closeChat,openPalette,closePalette,assistantBlocked,applyMunicipalitySearch,changeMunicipalityPage,openMunicipality,showMunicipalityTab,openProposalResult,openContractResult,S});boot();
