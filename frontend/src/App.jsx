import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [sheetList, setSheetList] = useState([]);
  const [selectedSheet, setSelectedSheet] = useState(null);
  const [sheetData, setSheetData] = useState([]);
  
  const [loadingList, setLoadingList] = useState(false);
  const [loadingData, setLoadingData] = useState(false);
  const [loadingMutation, setLoadingMutation] = useState(false);
  const [error, setError] = useState(null);

  // AI 템플릿 모달 상태
  const [showModal, setShowModal] = useState(false);
  const [newSheetTitle, setNewSheetTitle] = useState('');
  const [newSheetPrompt, setNewSheetPrompt] = useState('');

  // 히스토리 뷰어 상태
  const [showLogsModal, setShowLogsModal] = useState(false);
  const [logsList, setLogsList] = useState([]);

  // 컬럼 추가 모달 상태
  const [showColModal, setShowColModal] = useState(false);
  const [newColName, setNewColName] = useState('');

  // 행 추가 모달 상태
  const [showRowModal, setShowRowModal] = useState(false);
  const [newRowCount, setNewRowCount] = useState(1);

  // 표 수정 모달 상태
  const [showModifyModal, setShowModifyModal] = useState(false);
  const [modifyPrompt, setModifyPrompt] = useState('');

  // AI 밸런스 검사 모달 상태
  const [showAuditModal, setShowAuditModal] = useState(false);
  const [auditIssues, setAuditIssues] = useState([]);

  // 시트 연결 및 인증 정보
  const [activeSpreadsheetId, setActiveSpreadsheetId] = useState('1gVBHcmkSASco3rDXxjTGXfaMjiWRjYtavBDVP6o41ss'); // Default for demo
  const [inputSpreadsheetId, setInputSpreadsheetId] = useState('1gVBHcmkSASco3rDXxjTGXfaMjiWRjYtavBDVP6o41ss');
  const [serviceEmail, setServiceEmail] = useState('');

  const API_BASE = '/api/sheets';

  // 백엔드에서 서비스 이메일 등 설정 정보 불러오기
  const fetchConfig = async () => {
    try {
      const res = await fetch('/api/config/info');
      if (res.ok) {
        const data = await res.json();
        setServiceEmail(data.client_email);
      }
    } catch (err) {
      console.error("Config 로드 실패:", err);
    }
  };

  const fetchSheetList = async (targetId = activeSpreadsheetId) => {
    if (!targetId) return [];
    setLoadingList(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}?spreadsheet_id=${targetId}`);
      if (!response.ok) {
        throw new Error(`시트 목록 요청 실패: ${response.status}`);
      }
      const result = await response.json();
      const sheets = result.sheets || [];
      setSheetList(sheets);
      return sheets;
    } catch (err) {
      setError(err.message);
      return [];
    } finally {
      setLoadingList(false);
    }
  };

  useEffect(() => {
    fetchConfig();
    fetchSheetList(activeSpreadsheetId).then(sheets => {
      if (sheets.length > 0) fetchSheetData(sheets[0]);
    });
  }, [activeSpreadsheetId]);

  const fetchSheetData = async (sheetObj) => {
    if (!activeSpreadsheetId) return;
    setSelectedSheet(sheetObj);
    setLoadingData(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/${encodeURIComponent(sheetObj.title)}?spreadsheet_id=${activeSpreadsheetId}`);
      if (!response.ok) {
        throw new Error(`데이터 요청 실패: ${response.status}`);
      }
      const result = await response.json();
      setSheetData(result.data || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingData(false);
    }
  };

  const fetchLogs = async () => {
    if (!activeSpreadsheetId) return;
    try {
      const response = await fetch(`/api/action/logs?spreadsheet_id=${activeSpreadsheetId}`);
      if (response.ok) {
        const result = await response.json();
        setLogsList(result.logs || []);
      }
    } catch(err) {
      console.error(err);
    }
  };

  const clearLogs = async () => {
    if (!activeSpreadsheetId) return;
    const confirmAction = window.confirm("정말로 이 스프레드시트의 모든 히스토리 정보를 초기화하시겠습니까?\n이 작업은 되돌릴 수 없습니다.");
    if (!confirmAction) return;

    try {
      const response = await fetch(`/api/action/logs?spreadsheet_id=${activeSpreadsheetId}`, {
        method: 'DELETE'
      });
      if (response.ok) {
        alert("해당 시트의 히스토리가 완전히 초기화되었습니다.");
        fetchLogs();
      } else {
        throw new Error("초기화 실패");
      }
    } catch(err) {
      alert("히스토리 초기화 중 오류가 발생했습니다.");
    }
  };


  const handleMutation = async (url, method, description, bodyObj = null) => {
    if (!selectedSheet) return;
    if (method === 'DELETE') {
      const confirmAction = window.confirm(`정말로 ${description} 하시겠습니까?`);
      if (!confirmAction) return;
    }
    setLoadingMutation(true);
    setError(null);
    try {
      const options = { method };
      if (bodyObj) {
        options.headers = { 'Content-Type': 'application/json' };
        options.body = JSON.stringify(bodyObj);
      }
      
      const fetchUrl = url.includes('?') ? `${url}&spreadsheet_id=${activeSpreadsheetId}` : `${url}?spreadsheet_id=${activeSpreadsheetId}`;
      const response = await fetch(fetchUrl, options);
      if (!response.ok) {
        let errStr = `요청 실패: ${response.status}`;
        try {
          const errData = await response.json();
          if (errData.detail) errStr += ` - ${errData.detail}`;
        } catch (e) {}
        throw new Error(errStr);
      }
      await fetchSheetData(selectedSheet);
    } catch (err) {
      setError(`[${description} 실패] ` + err.message);
      alert(`[${description} 실패] ` + err.message);
    } finally {
      setLoadingMutation(false);
    }
  };

  const handleCreateAISheet = async () => {
    const title = newSheetTitle.trim();
    const promptTxt = newSheetPrompt.trim();
    if (!title || !promptTxt) {
      alert("시트 제목과 어떤 표를 원하는지 내용을 모두 입력해주세요.");
      return;
    }
    // 프론트엔드 중복 1차 검증
    if (sheetList.find(s => s.title === title)) {
      alert("이미 존재하는 시트 제목입니다. 다른 제목을 입력해주세요.");
      return;
    }

    setShowModal(false);
    setLoadingMutation(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE}/generate?spreadsheet_id=${activeSpreadsheetId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ new_sheet_title: title, prompt: promptTxt })
      });

      if (!response.ok) {
        let errStr = `시트 생성 실패: ${response.status}`;
        try {
          const errData = await response.json();
          if (errData.detail) errStr += ` - ${errData.detail}`;
        } catch(e){}
        throw new Error(errStr);
      }
      
      const result = await response.json();
      
      // 시트 목록 재패치 후, 방금 만든 시트로 강제 선택 이동
      const currentList = await fetchSheetList();
      const newlyCreated = currentList.find(s => s.title === result.title);
      if (newlyCreated) {
        fetchSheetData(newlyCreated);
      }
      
      // 입력 폼 초기화
      setNewSheetTitle('');
      setNewSheetPrompt('');
      alert("🎉 AI가 시트를 성공적으로 생성했습니다!");

    } catch (err) {
      setError(err.message);
      alert(err.message);
    } finally {
      setLoadingMutation(false);
    }
  };

  const handleUndo = async () => {
    setLoadingMutation(true);
    setError(null);
    try {
      const response = await fetch(`/api/action/undo?spreadsheet_id=${activeSpreadsheetId}`, {
        method: 'POST'
      });
      if (!response.ok) {
        let errStr = `되돌리기 실패: ${response.status}`;
        try {
          const errData = await response.json();
          if (errData.detail) errStr += ` - ${errData.detail}`;
        } catch (e) {}
        throw new Error(errStr);
      }
      
      const result = await response.json();
      
      if (result.restoredType === "ADD_SHEET") {
        const sheets = await fetchSheetList();
        if (sheets.length > 0) fetchSheetData(sheets[0]);
        else setSheetData([]);
      } else {
        await fetchSheetData(selectedSheet);
      }
    } catch (err) {
      setError(err.message);
      alert(err.message);
    } finally {
      setLoadingMutation(false);
    }
  };

  const handleRedo = async () => {
    setLoadingMutation(true);
    setError(null);
    try {
      const response = await fetch(`/api/action/redo?spreadsheet_id=${activeSpreadsheetId}`, {
        method: 'POST'
      });
      if (!response.ok) {
        let errStr = `앞으로 돌리기 실패: ${response.status}`;
        try {
          const errData = await response.json();
          if (errData.detail) errStr += ` - ${errData.detail}`;
        } catch (e) {}
        throw new Error(errStr);
      }
      
      const result = await response.json();
      
      if (result.restoredType === "ADD_SHEET") {
        const sheets = await fetchSheetList();
        const newlyCreated = sheets.find(s => s.title === result.title);
        if (newlyCreated) fetchSheetData(newlyCreated);
      } else {
        await fetchSheetData(selectedSheet);
      }
    } catch (err) {
      setError(err.message);
      alert(err.message);
    } finally {
      setLoadingMutation(false);
    }
  };

  const handleRenameSheet = async () => {
    if (!selectedSheet) return;
    const newName = window.prompt("새로운 시트 이름을 입력하세요", selectedSheet.title);
    if (!newName || newName.trim() === "" || newName === selectedSheet.title) return;

    setLoadingMutation(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/${selectedSheet.sheetId}/rename?spreadsheet_id=${activeSpreadsheetId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ new_title: newName.trim() })
      });
      
      if (!response.ok) {
        let errStr = "이름 변경 실패";
        try {
          const errData = await response.json();
          errStr += `: ${errData.detail || response.statusText}`;
        } catch {
          errStr +=  `: ${response.status}`;
        }
        throw new Error(errStr);
      }
      
      // 이름 변경 성공 시 좌측 사이드바와 현재 시트 데이터를 전부 갱신
      await fetchSheetList(activeSpreadsheetId);
      // 제목을 바꿨으므로, selectedSheet 객체도 업데이트된 이름으로 가져올 필요가 있음.
      // fetchSheetList 가 끝난 후 배열에서 찾아서 갱신
      const updatedList = await (await fetch(`${API_BASE}?spreadsheet_id=${activeSpreadsheetId}`)).json();
      const updatedSheet = updatedList.sheets.find(s => s.sheetId === selectedSheet.sheetId);
      if (updatedSheet) fetchSheetData(updatedSheet);
      
    } catch (err) {
      console.error(err);
      alert(err.message);
    } finally {
      setLoadingMutation(false);
    }
  };

  const executeAddRow = () => {
    let count = parseInt(newRowCount, 10);
    if (isNaN(count) || count < 1) {
      alert("생성할 줄 수를 올바르게 입력해주세요 (최소 1줄).");
      return;
    }
    if (count > 10) {
      alert("AI 추론 안전을 위해 한 번에 최대 10줄까지만 생성 가능합니다.");
      count = 10;
    }
    setShowRowModal(false);
    handleMutation(`${API_BASE}/${selectedSheet.sheetId}/rows`, 'POST', `AI 튜닝 행 ${count}줄 생성`, { num_rows: count });
  };
  
  const executeAddColumn = () => {
    if (!newColName || newColName.trim() === '') {
      alert("열 제목을 입력해주세요.");
      return;
    }
    const targetName = newColName.trim();
    setShowColModal(false);
    setNewColName('');
    handleMutation(`${API_BASE}/${selectedSheet.sheetId}/columns`, 'POST', 'AI 열 생성', { new_column_name: targetName });
  };

  const executeModifySheet = () => {
    if (!modifyPrompt || modifyPrompt.trim() === '') {
      alert("전체 표 프롬프트를 작성해주세요.");
      return;
    }
    const targetPrompt = modifyPrompt.trim();
    setShowModifyModal(false);
    setModifyPrompt('');
    handleMutation(`${API_BASE}/${selectedSheet.sheetId}/modify`, 'POST', 'AI 표 전체 일괄 수정', { prompt: targetPrompt });
  };
  const deleteRow = (rowIndex) => handleMutation(`${API_BASE}/${selectedSheet.sheetId}/rows/${rowIndex}`, 'DELETE', '선택된 행 삭제');
  const deleteColumn = (colIndex) => handleMutation(`${API_BASE}/${selectedSheet.sheetId}/columns/${colIndex}`, 'DELETE', '선택된 열 삭제');

  const downloadJSON = () => {
    if (!sheetData || sheetData.length === 0) {
      alert("다운로드할 데이터가 없거나 올바르지 않습니다.");
      return;
    }
    const dataStr = JSON.stringify(sheetData, null, 2);
    const blob = new Blob([dataStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${selectedSheet.title || "sheet"}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const downloadCSV = () => {
    if (!sheetData || sheetData.length === 0) {
      alert("다운로드할 데이터가 없거나 올바르지 않습니다.");
      return;
    }
    const headersList = Object.keys(sheetData[0]);
    const csvRows = [];
    csvRows.push(headersList.map(h => `"${(h || "").toString().replace(/"/g, '""')}"`).join(","));
    
    for (const row of sheetData) {
      const values = headersList.map(h => {
        const val = row[h] !== null && row[h] !== undefined ? row[h] : "";
        return `"${val.toString().replace(/"/g, '""')}"`;
      });
      csvRows.push(values.join(","));
    }
    
    // UTF-8 BOM 추가하여 엑셀에서 한글 깨짐 방지
    const csvString = "\uFEFF" + csvRows.join("\n");
    const blob = new Blob([csvString], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${selectedSheet.title || "sheet"}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const headers = sheetData.length > 0 ? Object.keys(sheetData[0]) : [];

  const handleAudit = async () => {
    if (!selectedSheet) return;
    setLoadingMutation(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/${selectedSheet.sheetId}/audit?spreadsheet_id=${activeSpreadsheetId}`, {
        method: 'POST'
      });
      if (!response.ok) {
        let errStr = "밸런스 검수 오류";
        try {
          const errData = await response.json();
          errStr += `: ${errData.detail || response.statusText}`;
        } catch {
          errStr +=  `: ${response.status}`;
        }
        throw new Error(errStr);
      }
      const data = await response.json();
      setAuditIssues(data.issues || []);
      setShowAuditModal(true);
    } catch (err) {
      alert(`[검수 실패] ${err.message}`);
    } finally {
      setLoadingMutation(false);
    }
  };

  return (
    <div style={{ display: 'flex', minHeight: '100vh', fontFamily: 'sans-serif' }}>
      
      {/* 🟢 좌측 사이드바 */}
      <div style={{ 
        width: '250px', 
        borderRight: '1px solid #ddd', 
        padding: '2rem 1rem',
        backgroundColor: '#fafafa',
        display: 'flex',
        flexDirection: 'column'
      }}>
        <h1 style={{ 
          fontSize: '1.5rem', 
          fontWeight: '800', 
          margin: '0 0 1.5rem 0', 
          color: '#333',
          letterSpacing: '-0.5px'
        }}>
          Super-Balance <span style={{ color: '#6f42c1' }}>AI</span>
        </h1>

        <button 
          onClick={() => setShowModal(true)}
          style={{...btnStyle('#6f42c1'), marginBottom: '1.5rem', width: '100%', fontSize: '1rem', padding: '12px'}}
        >
          ✨ AI 템플릿 시트 생성
        </button>

        <h2 style={{ marginTop: 0, fontSize: '1.2rem', paddingBottom: '1rem', borderBottom: '2px solid #ddd' }}>
          연결된 스프레드시트 설정
        </h2>
        
        <div style={{ marginBottom: '1.5rem', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <button 
            onClick={() => {
              navigator.clipboard.writeText(serviceEmail);
              alert('서비스 봇 이메일이 복사되었습니다: ' + serviceEmail);
            }}
            style={{ 
              ...btnStyle('#343a40'), 
              fontSize: '12px', padding: '6px', width: '100%', wordBreak: 'break-all'
            }}
            title="클릭하여 서비스 계정 이메일 복사"
          >
            📋 공유 이메일 복사 (클릭)
          </button>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <label style={{ fontSize: '11px', fontWeight: 'bold', color: '#555' }}>
              시트 ID (URL의 긴 문자열)
            </label>
            <input 
              value={inputSpreadsheetId}
              onChange={e => setInputSpreadsheetId(e.target.value)}
              placeholder="스프레드시트 ID 입력"
              style={{ padding: '6px', fontSize: '12px', border: '1px solid #ccc', borderRadius: '4px' }}
            />
            <button 
              onClick={() => {
                if(inputSpreadsheetId.trim()){
                  setActiveSpreadsheetId(inputSpreadsheetId.trim());
                  setSheetList([]);
                  setSheetData([]);
                  setSelectedSheet(null);
                }
              }}
              style={{...btnStyle('#007bff'), fontSize:'12px', padding:'6px'}}
            >
              [ 연결 적용하기 ]
            </button>
          </div>
        </div>

        <h2 style={{ marginTop: 0, fontSize: '1.2rem', paddingBottom: '1rem', borderBottom: '2px solid #ddd' }}>
          시트 목록
        </h2>
        
        {loadingList && <p>목록 불러오는 중...</p>}
        {error && !loadingMutation && <p style={{ color: 'red', fontSize: '14px' }}>{error}</p>}
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '1rem', overflowY: 'auto' }}>
          {sheetList.map((sheet, idx) => {
             const isSelected = selectedSheet?.sheetId === sheet.sheetId;
             return (
              <button
                key={idx}
                onClick={() => fetchSheetData(sheet)}
                style={{
                  padding: '10px',
                  textAlign: 'left',
                  backgroundColor: isSelected ? '#007bff' : 'white',
                  color: isSelected ? 'white' : 'black',
                  border: '1px solid #ccc',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontWeight: isSelected ? 'bold' : 'normal',
                  transition: 'background-color 0.2s'
                }}
              >
                📄 {sheet.title}
              </button>
            );
          })}
        </div>
      </div>

      {/* 🟢 우측 메인 영역 */}
      <div style={{ flex: 1, padding: '2rem', overflowX: 'auto', position: 'relative' }}>
        
        {/* 💎 Premium Loading Overlay */}
        {loadingMutation && (
          <div className="loading-overlay">
            <div className="loading-card">
              <div className="loading-spinner"></div>
              <p className="loading-text">🤖 AI가 데이터를 정밀하게 조율 중입니다...</p>
              <p style={{ fontSize: '0.9rem', color: '#666', marginTop: '-10px' }}>잠시만 기다려 주세요.</p>
            </div>
          </div>
        )}

        {/* 상단 액션 복구 및 다운로드 영역 */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', borderBottom: '1px solid #eee', paddingBottom: '1rem' }}>
          <div style={{ display: 'flex', gap: '10px' }}>
            {selectedSheet && !loadingData && sheetData.length > 0 && (
              <>
                <button onClick={downloadCSV} style={{...btnStyle('#6c757d'), whiteSpace: 'nowrap', padding: '6px 12px', fontSize: '0.9rem'}} title="UTF-8 CSV 형식으로 다운로드">⬇️ CSV</button>
                <button onClick={downloadJSON} style={{...btnStyle('#6c757d'), whiteSpace: 'nowrap', padding: '6px 12px', fontSize: '0.9rem'}} title="JSON 배열 형식으로 다운로드">⬇️ JSON</button>
              </>
            )}
          </div>
          
          <div style={{ display: 'flex', gap: '10px' }}>
            <button 
              onClick={() => { fetchLogs(); setShowLogsModal(true); }} 
              style={{...btnStyle('#343a40'), padding: '6px 12px', fontSize: '0.9rem', whiteSpace: 'nowrap'}}
              title="DB에 저장된 전체 작업 이력 열람"
            >
              📜 작업 로그 조회
            </button>
            <button 
              onClick={handleUndo} 
              style={{...btnStyle('#ff5722'), padding: '6px 12px', fontSize: '0.9rem', whiteSpace: 'nowrap'}}
              title="방금 처리한 내용을 되돌립니다 (Undo)"
            >
              ↩️
            </button>
            <button 
              onClick={handleRedo} 
              style={{...btnStyle('#2e7d32'), padding: '6px 12px', fontSize: '0.9rem', whiteSpace: 'nowrap'}}
              title="취소했던 내용을 다시 살려냅니다 (Redo)"
            >
              ↪️
            </button>
          </div>
        </div>

        {/* 테이블 타이틀 및 도구 영역 */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '15px', marginBottom: '15px' }}>
          <div>
            {selectedSheet ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <h2 style={{ margin: 0 }}>{selectedSheet.title}</h2>
                <button 
                  onClick={handleRenameSheet}
                  style={{ background: 'transparent', border: 'none', cursor: 'pointer', fontSize: '18px', padding: 0 }}
                  title="시트 이름 변경"
                >
                  ✏️
                </button>
              </div>
            ) : (
              <h2 style={{ margin: 0 }}>시트를 선택해 주세요</h2>
            )}
          </div>
          
          {selectedSheet && !loadingData && (
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button onClick={() => { setModifyPrompt(''); setShowModifyModal(true); }} style={{...btnStyle('#17a2b8'), whiteSpace: 'nowrap'}}>
                📝 AI 표 전체 수정
              </button>
              <button onClick={() => { setNewColName(''); setShowColModal(true); }} style={{...btnStyle('#28a745'), whiteSpace: 'nowrap'}}>+ AI 열 생성</button>
              <button onClick={() => { setNewRowCount(1); setShowRowModal(true); }} style={{...btnStyle('#007bff'), whiteSpace: 'nowrap'}}>+ AI 행 생성</button>
              <button onClick={handleAudit} style={{...btnStyle('#dc3545'), whiteSpace: 'nowrap'}} title="데이터를 스캔하여 비정상치 밸런스를 찾습니다.">⚠️ AI 밸런스 검사</button>
            </div>
          )}
        </div>
        
        {loadingData && <p>데이터를 불러오는 중입니다...</p>}
        {!loadingData && sheetData.length === 0 && selectedSheet && (
          <div style={{ padding: '20px', background: '#f8f9fa', borderRadius: '8px' }}>
            <p style={{ color: '#666' }}>현재 시트에 데이터가 비어있습니다.</p>
            <button onClick={() => { setNewRowCount(1); setShowRowModal(true); }} style={btnStyle('#007bff')}>무작정 첫 데이터(AI 자동) 추가해보기</button>
          </div>
        )}

        {!loadingData && sheetData.length > 0 && (
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'center' }}>
            <thead>
              <tr style={{ backgroundColor: '#f4f4f4' }}>
                {headers.map((header, idx) => (
                  <th key={header} style={thStyle}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span>{header}</span>
                      <button onClick={() => deleteColumn(idx)} style={delBtnStyle} title="열 삭제">🗑</button>
                    </div>
                  </th>
                ))}
                <th style={{ ...thStyle, width: '60px' }}>관리</th>
              </tr>
            </thead>
            <tbody>
              {sheetData.map((row, index) => (
                <tr key={index} style={{ borderBottom: '1px solid #ddd' }}>
                  {headers.map((header) => (
                    <td key={header} style={tdStyle}>{row[header] || ''}</td>
                  ))}
                  <td style={tdStyle}>
                    <button onClick={() => deleteRow(index + 1)} style={delBtnStyle} title="행 삭제">🗑</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* 🟣 AI 자동 생성 모달 UI */}
      {showModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.6)',
          display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 10000
        }}>
          <div style={{
            background: 'white', padding: '30px', borderRadius: '12px', width: '400px',
            boxShadow: '0 4px 15px rgba(0,0,0,0.2)', display: 'flex', flexDirection: 'column', gap: '15px'
          }}>
            <h2 style={{ margin: 0 }}>✨ AI 템플릿 시트 생성</h2>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
              <label style={{ fontWeight: 'bold' }}>시트 제목 (Sheet Title)</label>
              <input 
                value={newSheetTitle} 
                onChange={e => setNewSheetTitle(e.target.value)} 
                placeholder="예: 캐주얼 게임 스테이지 난이도, 신규 무기 스펙 테이블"
                style={{ padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
              />
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
              <label style={{ fontWeight: 'bold' }}>어떤 표를 원하시나요? (Prompt)</label>
              <textarea 
                rows={4}
                value={newSheetPrompt} 
                onChange={e => setNewSheetPrompt(e.target.value)} 
                placeholder="예: 플레이어가 1~5판까지 만날 수 있는 몬스터들의 이름, 체력, 공격력, 이동 속도, 그리고 클리어 보상 골드를 수평 밸런스에 맞게 표로 디자인해서 짜줘"
                style={{ padding: '8px', border: '1px solid #ccc', borderRadius: '4px', resize: 'vertical' }}
              />
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
              <button onClick={() => setShowModal(false)} style={btnStyle('#6c757d')}>취소</button>
              <button onClick={handleCreateAISheet} style={btnStyle('#28a745')}>자동 생성 시작</button>
            </div>
          </div>
        </div>
      )}

      {/* 📜 DB 작업 로그 모달 UI */}
      {showLogsModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.6)',
          display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 10000
        }}>
          <div style={{
            background: 'white', padding: '30px', borderRadius: '12px', width: '500px', maxHeight: '70vh',
            boxShadow: '0 4px 15px rgba(0,0,0,0.2)', display: 'flex', flexDirection: 'column', gap: '15px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                <h2 style={{ margin: 0 }}>📜 PostgreSQL 영구 히스토리 로그</h2>
                <button onClick={() => { fetchLogs(); }} style={{background:'transparent', border:'none', cursor:'pointer', fontSize:'1.2rem', color:'#007bff'}} title="새로고침">🔄</button>
              </div>
              <button 
                onClick={clearLogs} 
                style={{...btnStyle('#dc3545'), fontSize: '12px', padding: '4px 8px'}}
                title="이 스프레드시트의 전체 기록을 삭제합니다"
              >
                히스토리 초기화 (Clear)
              </button>
            </div>
            
            <p style={{ fontSize: '13px', color: '#666', margin: 0 }}>회색(취소선)으로 표시된 내역은 이미 Undo 되어 Redo 스택 큐로 넘어가 있는 작업입니다.</p>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '5px', overflowY: 'auto', border: '1px solid #ddd', padding: '10px', flex: 1 }}>
              {logsList.length === 0 ? (
                <p style={{ textAlign: 'center', color: '#999' }}>히스토리 기록이 없습니다.</p>
              ) : (
                logsList.map((log) => {
                  return (
                    <div key={log.id} style={{
                      padding: '12px', 
                      borderBottom: '1px solid #eee', 
                      backgroundColor: log.is_undone ? '#f8f9fa' : '#fff',
                      opacity: log.is_undone ? 0.5 : 1,
                      textDecoration: log.is_undone ? 'line-through' : 'none',
                      display: 'flex', flexDirection: 'column', gap: '6px'
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <span style={{ fontWeight: 'bold', fontSize: '15px', color: log.is_undone ? '#888' : '#212529', lineHeight: '1.4' }}>
                          {log.summary || "내용 없음"}
                        </span>
                        <span style={{ fontSize: '11px', color: '#888', whiteSpace: 'nowrap', marginLeft: '10px' }}>
                          {new Date(log.created_at).toLocaleString()}
                        </span>
                      </div>
                      <div>
                        <span style={{ 
                          fontSize: '10px', 
                          backgroundColor: log.is_undone ? '#e9ecef' : '#e7f1ff', 
                          color: log.is_undone ? '#6c757d' : '#0d6efd', 
                          padding: '3px 6px', 
                          borderRadius: '12px', 
                          fontWeight: 'bold',
                          textDecoration: 'none'
                        }}>
                          {log.action_type}
                        </span>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '10px' }}>
              <button onClick={() => setShowLogsModal(false)} style={btnStyle('#6c757d')}>닫기</button>
            </div>
          </div>
        </div>
      )}

      {/* 🔴 AI 열 추가 모달 (Input) */}
      {showColModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.6)',
          display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 10000
        }}>
          <div style={{
            background: 'white', padding: '30px', borderRadius: '12px', width: '400px',
            boxShadow: '0 4px 15px rgba(0,0,0,0.2)', display: 'flex', flexDirection: 'column', gap: '15px'
          }}>
            <h2 style={{ margin: 0 }}>+ AI 열 추가 생성</h2>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
              <label style={{ fontWeight: 'bold' }}>새로운 열의 제목을 입력하세요</label>
              <input 
                value={newColName} 
                onChange={e => setNewColName(e.target.value)} 
                onKeyDown={e => { if(e.key === 'Enter') executeAddColumn(); }}
                placeholder="예: 치명타 확률, 이동 속도, 드롭 아이템, 획득 골드 등"
                style={{ padding: '10px', border: '1px solid #ccc', borderRadius: '4px', fontSize: '15px' }}
                autoFocus
              />
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
              <button onClick={() => setShowColModal(false)} style={btnStyle('#6c757d')}>취소</button>
              <button onClick={executeAddColumn} style={btnStyle('#28a745')}>AI 열 생성 (10초 대기)</button>
            </div>
          </div>
        </div>
      )}

      {/* 🟢 AI 다중 행 생성 모달 (Number) */}
      {showRowModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.6)',
          display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 10000
        }}>
          <div style={{
            background: 'white', padding: '30px', borderRadius: '12px', width: '380px',
            boxShadow: '0 4px 15px rgba(0,0,0,0.2)', display: 'flex', flexDirection: 'column', gap: '15px'
          }}>
            <h2 style={{ margin: 0, color: '#007bff' }}>+ AI 다중 행 일괄 생성</h2>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
              <label style={{ fontWeight: 'bold', fontSize: '14px' }}>한 번에 몇 줄의 새로운 데이터를 만들까요?</label>
              <p style={{ margin: 0, fontSize: '12px', color: '#666' }}>최대 10줄까지 한 번에 예측 생성할 수 있습니다.</p>
              <input 
                type="number"
                min="1"
                max="10"
                value={newRowCount} 
                onChange={e => setNewRowCount(e.target.value)} 
                onKeyDown={e => { if(e.key === 'Enter') executeAddRow(); }}
                style={{ padding: '10px', border: '1px solid #ccc', borderRadius: '4px', fontSize: '18px', textAlign: 'center', fontWeight: 'bold' }}
                autoFocus
              />
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
              <button onClick={() => setShowRowModal(false)} style={btnStyle('#6c757d')}>취소</button>
              <button onClick={executeAddRow} style={btnStyle('#007bff')}>N줄 일괄 생성 (20초 대기)</button>
            </div>
          </div>
        </div>
      )}

      {/* 🔵 AI 표 일괄 수정 모달 (Textarea) */}
      {showModifyModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.6)',
          display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 10000
        }}>
          <div style={{
            background: 'white', padding: '30px', borderRadius: '12px', width: '500px',
            boxShadow: '0 4px 15px rgba(0,0,0,0.2)', display: 'flex', flexDirection: 'column', gap: '15px'
          }}>
            <h2 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>📝</span> AI 표 전체 일괄 수정
            </h2>
            <p style={{ margin: 0, color: '#555', fontSize: '14px', lineHeight: '1.5' }}>
              현재까지 누적된 전체 표 데이터를 바탕으로,<br/>AI에게 밸런스 조정이나 일괄 번역 명령을 내립니다.
            </p>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
              <textarea 
                rows={5}
                value={modifyPrompt} 
                onChange={e => setModifyPrompt(e.target.value)} 
                placeholder="예: 모든 몬스터의 획득 골드를 2배씩 뻥튀기시켜줘 / 영웅 등급 무기의 공격력을 20% 늘려 등"
                style={{ padding: '10px', border: '1px solid #ccc', borderRadius: '4px', resize: 'vertical', fontSize: '15px', lineHeight:'1.4' }}
                autoFocus
              />
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
              <button onClick={() => setShowModifyModal(false)} style={btnStyle('#6c757d')}>취소</button>
              <button onClick={executeModifySheet} style={btnStyle('#17a2b8')}>AI 전체 변환 (15초 대기)</button>
            </div>
          </div>
        </div>
      )}

      {/* ⚠️ AI 밸런스 검사 결과 모달 UI */}
      {showAuditModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.6)',
          display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 10000
        }}>
          <div style={{
            background: 'white', padding: '30px', borderRadius: '12px', width: '500px', maxHeight: '70vh',
            boxShadow: '0 4px 15px rgba(0,0,0,0.2)', display: 'flex', flexDirection: 'column', gap: '15px'
          }}>
            <h2 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px', color: '#dc3545' }}>
              <span>⚠️</span> AI 밸런스 검사 리포트
            </h2>
            <p style={{ margin: 0, color: '#555', fontSize: '14px', lineHeight: '1.5' }}>
              시트 내의 데이터들을 교차 비교하여 발견된 수치적 불균형 의심 항목입니다.
            </p>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', overflowY: 'auto', border: '1px solid #ddd', padding: '10px', flex: 1, backgroundColor: '#fdfdfd' }}>
              {auditIssues.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '20px', color: '#28a745', fontWeight: 'bold' }}>
                  🎉 기획 데이터에 특이한 밸런스 붕괴 요소가 발견되지 않았습니다.
                </div>
              ) : (
                auditIssues.map((issueItem, idx) => (
                  <div key={idx} style={{ padding: '10px', borderLeft: '4px solid #dc3545', backgroundColor: '#fff', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
                    <div style={{ fontWeight: 'bold', fontSize: '13px', color: '#dc3545', marginBottom: '4px' }}>행 번호: {issueItem.row_index}</div>
                    <div style={{ fontSize: '14px', lineHeight: '1.4' }}>{issueItem.issue}</div>
                  </div>
                ))
              )}
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '10px' }}>
              <button onClick={() => setShowAuditModal(false)} style={btnStyle('#6c757d')}>닫기</button>
            </div>
          </div>
        </div>
      )}

    </div>
  )
}

const btnStyle = (color) => ({
  backgroundColor: color, color: 'white', border: 'none', padding: '8px 16px', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold'
});

const thStyle = { 
  border: '1px solid #ddd', 
  padding: '10px 15px', 
  whiteSpace: 'nowrap', 
  fontSize: '14px' 
};

const tdStyle = { 
  border: '1px solid #ddd', 
  padding: '10px 15px', 
  whiteSpace: 'nowrap', 
  fontSize: '14px' 
};

const delBtnStyle = { background: 'transparent', border: 'none', cursor: 'pointer', fontSize: '1rem', color: '#dc3545', padding: '0 4px' };

export default App
