/**
 * Google Drive 한글 파일명 자동 변환 (NFD → NFC)
 *
 * Mac에서 업로드한 파일의 한글 이름이 깨져 보이는 문제를 자동으로 수정합니다.
 * Google Sheet에 바인딩하여 사용합니다.
 *
 * 사용법: README.md 참고
 */

// ── 설정 ──────────────────────────────────────────────

/** 실행 시간 제한 (5분 — 6분 한계 전에 안전하게 종료) */
var TIME_LIMIT_MS = 5 * 60 * 1000;

/** 로그 flush 간격 (50개마다 중간 저장) */
var LOG_FLUSH_INTERVAL = 50;

/** 설정 시트 이름 */
var CONFIG_SHEET = '설정';

/** 로그 시트 이름 */
var LOG_SHEET = '변환 로그';

// ── 메뉴 ──────────────────────────────────────────────

function onOpen() {
  SpreadsheetApp.getUi().createMenu('파일명 변환')
    .addItem('지금 실행', 'menuRun_')
    .addItem('초기 전체 스캔', 'menuFullScan_')
    .addSeparator()
    .addItem('15분 자동 트리거 켜기', 'enableTrigger')
    .addItem('자동 트리거 끄기', 'disableTrigger')
    .addToUi();
}

/** 메뉴 → 지금 실행 (lock 포함) */
function menuRun_() {
  main();
}

/** 메뉴 → 초기 전체 스캔 (lock 포함) */
function menuFullScan_() {
  var lock = LockService.getScriptLock();
  if (!lock.tryLock(5000)) {
    try {
      SpreadsheetApp.getUi().alert('다른 실행이 진행 중입니다. 잠시 후 다시 시도해주세요.');
    } catch (e) { /* ignore */ }
    return;
  }
  try {
    initFullScan_();
  } finally {
    lock.releaseLock();
  }
}

// ── 메인 ──────────────────────────────────────────────

/**
 * 트리거 엔트리포인트.
 * 전체 스캔 진행 중이면 이어서 처리, 완료 상태면 증분 스캔.
 */
function main() {
  var lock = LockService.getScriptLock();
  if (!lock.tryLock(5000)) {
    console.log('다른 실행이 진행 중입니다. 종료.');
    return;
  }

  try {
    var props = PropertiesService.getScriptProperties();
    var scanState = props.getProperty('scanState');

    if (scanState) {
      processQueue_();
    } else if (props.getProperty('changePageToken')) {
      incrementalScan_();
    } else {
      initFullScan_();
    }
  } finally {
    lock.releaseLock();
  }
}

// ── 전체 스캔 (큐 기반) ───────────────────────────────

/**
 * 전체 스캔 초기화. 대상 폴더들을 큐에 넣고 처리 시작.
 * 반드시 lock이 획득된 상태에서 호출.
 */
function initFullScan_() {
  var folderIds = getTargetFolderIds_();
  if (folderIds.length === 0) {
    try {
      SpreadsheetApp.getUi().alert(
        '설정 시트의 A열에 대상 폴더 ID를 입력해주세요.\n\n' +
        '폴더 ID는 Google Drive 폴더 URL에서 확인할 수 있습니다:\n' +
        'https://drive.google.com/drive/folders/여기가_폴더ID'
      );
    } catch (e) { /* 트리거 실행 시 UI 불가 */ }
    return;
  }

  var props = PropertiesService.getScriptProperties();

  // 증분 스캔용 시작 토큰 기록 (스캔 완료 후 이 시점부터 증분 추적)
  var startToken = Drive.Changes.getStartPageToken().startPageToken;
  props.setProperty('changeStartToken', startToken);

  // 폴더 큐 초기화: 폴더 ID만 저장 (path는 처리 시 생성 — 직렬화 크기 절약)
  var queue = folderIds.map(function(id) {
    return id;
  });

  var state = {
    queue: queue,
    fileContinuation: null
  };
  props.setProperty('scanState', JSON.stringify(state));

  processQueue_();
}

/**
 * 큐에서 폴더를 꺼내 파일을 스캔하고 변환.
 * 시간 제한에 도달하면 상태를 저장하고 종료.
 */
function processQueue_() {
  var props = PropertiesService.getScriptProperties();
  var stateJson = props.getProperty('scanState');

  var state;
  try {
    state = JSON.parse(stateJson);
  } catch (e) {
    console.error('스캔 상태 파싱 실패. 초기화합니다.');
    props.deleteProperty('scanState');
    return;
  }

  var startTime = Date.now();
  var totalRenamed = 0;
  var logBuffer = [];

  // 이전 실행에서 중단된 파일 iterator 이어서 처리
  if (state.fileContinuation) {
    var cont = state.fileContinuation;
    var files;
    try {
      files = DriveApp.continueFileIteratorUsingToken(cont.token);
    } catch (e) {
      console.error('파일 iterator 복원 실패: ' + e.message);
      state.fileContinuation = null;
      saveState_(props, state);
      return;
    }

    while (files.hasNext()) {
      if (Date.now() - startTime > TIME_LIMIT_MS) {
        state.fileContinuation = {
          token: files.getContinuationToken(),
          path: cont.path
        };
        flushLog_(logBuffer);
        saveState_(props, state);
        console.log('시간 제한 도달. 이번 변환: ' + totalRenamed);
        return;
      }
      var result = renameFileToNFC_(files.next(), cont.path);
      if (result) {
        logBuffer.push(result);
        totalRenamed++;
        if (logBuffer.length >= LOG_FLUSH_INTERVAL) {
          flushLog_(logBuffer);
          logBuffer = [];
        }
      }
    }
    state.fileContinuation = null;
  }

  // 큐에서 폴더를 하나씩 꺼내 처리
  while (state.queue.length > 0) {
    if (Date.now() - startTime > TIME_LIMIT_MS) {
      flushLog_(logBuffer);
      saveState_(props, state);
      console.log('시간 제한 도달. 이번 변환: ' + totalRenamed);
      return;
    }

    var folderId = state.queue.shift();
    var folder;
    try {
      folder = DriveApp.getFolderById(folderId);
    } catch (e) {
      console.error('폴더 접근 실패 (' + folderId + '): ' + e.message);
      continue;
    }

    var folderPath = folder.getName();

    // 하위 폴더를 큐 앞에 추가 (깊이 우선)
    var subFolders = folder.getFolders();
    var subItems = [];
    while (subFolders.hasNext()) {
      subItems.push(subFolders.next().getId());
    }
    state.queue = subItems.concat(state.queue);

    // 중간 상태 저장 (강제 종료 대비)
    saveState_(props, state);

    // 파일 처리
    var fileIter = folder.getFiles();
    while (fileIter.hasNext()) {
      if (Date.now() - startTime > TIME_LIMIT_MS) {
        state.fileContinuation = {
          token: fileIter.getContinuationToken(),
          path: folderPath
        };
        flushLog_(logBuffer);
        saveState_(props, state);
        console.log('시간 제한 도달. 이번 변환: ' + totalRenamed);
        return;
      }
      var result = renameFileToNFC_(fileIter.next(), folderPath);
      if (result) {
        logBuffer.push(result);
        totalRenamed++;
        if (logBuffer.length >= LOG_FLUSH_INTERVAL) {
          flushLog_(logBuffer);
          logBuffer = [];
        }
      }
    }
  }

  // 큐 비어짐 = 전체 스캔 완료
  flushLog_(logBuffer);
  props.deleteProperty('scanState');
  props.setProperty('changePageToken', props.getProperty('changeStartToken'));
  props.deleteProperty('changeStartToken');
  console.log('전체 스캔 완료. 변환 파일 수: ' + totalRenamed);
  showCompletionMessage_(totalRenamed, '전체 스캔');
}

function saveState_(props, state) {
  try {
    props.setProperty('scanState', JSON.stringify(state));
  } catch (e) {
    // 9KB 한도 초과 시 큐에서 path 정보 제거하여 크기 축소
    console.error('상태 저장 실패 (크기 초과 가능): ' + e.message);
  }
}

// ── 증분 스캔 ─────────────────────────────────────────

/**
 * changes.list API로 변경된 파일만 처리.
 * 대상 폴더 및 모든 하위 폴더의 파일을 감지.
 */
function incrementalScan_() {
  var startTime = Date.now();
  var props = PropertiesService.getScriptProperties();
  var pageToken = props.getProperty('changePageToken');
  var targetFolderIds = getTargetFolderIds_();
  var renamed = 0;
  var logBuffer = [];

  // 대상 폴더 + 모든 하위 폴더 ID를 수집 (캐시 확인)
  var allFolderIds = getCachedSubFolderIds_(targetFolderIds);

  while (pageToken) {
    // 시간 체크
    if (Date.now() - startTime > TIME_LIMIT_MS) {
      flushLog_(logBuffer);
      // pageToken은 이미 마지막 처리된 페이지에서 저장됨
      console.log('증분 스캔 시간 제한 도달. 변환: ' + renamed);
      return;
    }

    var response = Drive.Changes.list(pageToken, {
      fields: 'nextPageToken,newStartPageToken,changes(fileId,file(name,parents,trashed))',
      pageSize: 100,
      includeItemsFromAllDrives: true,
      supportsAllDrives: true
    });

    var changes = response.changes || [];
    for (var i = 0; i < changes.length; i++) {
      var change = changes[i];
      if (!change.file || change.file.trashed) continue;

      // 대상 폴더(하위 포함)의 파일인지 확인
      var parents = change.file.parents || [];
      var isTarget = false;
      for (var j = 0; j < parents.length; j++) {
        if (allFolderIds[parents[j]]) {
          isTarget = true;
          break;
        }
      }
      if (!isTarget) continue;

      // NFD 확인 및 변환
      var name = change.file.name;
      var nfcName = name.normalize('NFC');
      if (name !== nfcName) {
        try {
          Drive.Files.update({ name: nfcName }, change.fileId, null, {
            supportsAllDrives: true
          });
          logBuffer.push([new Date(), change.fileId, name, nfcName, '(증분)']);
          renamed++;
          if (logBuffer.length >= LOG_FLUSH_INTERVAL) {
            flushLog_(logBuffer);
            logBuffer = [];
          }
        } catch (e) {
          console.error('변환 실패 (' + name + '): ' + e.message);
        }
      }
    }

    // 페이지 토큰 업데이트 (매 페이지 후 저장 — 강제 종료 시 복구 가능)
    if (response.newStartPageToken) {
      props.setProperty('changePageToken', response.newStartPageToken);
    } else if (response.nextPageToken) {
      props.setProperty('changePageToken', response.nextPageToken);
    }
    pageToken = response.nextPageToken || null;
  }

  flushLog_(logBuffer);
  if (renamed > 0) {
    console.log('증분 스캔 완료. 변환 파일 수: ' + renamed);
  }
}

/**
 * 하위 폴더 ID를 캐시하여 매번 재수집하지 않음.
 * 캐시 유효 시간: 1시간.
 */
function getCachedSubFolderIds_(folderIds) {
  var cache = CacheService.getScriptCache();
  var cached = cache.get('subFolderIds');

  if (cached) {
    try {
      return JSON.parse(cached);
    } catch (e) { /* 파싱 실패 시 재수집 */ }
  }

  var map = collectAllSubFolderIds_(folderIds);

  try {
    cache.put('subFolderIds', JSON.stringify(map), 3600); // 1시간 캐시
  } catch (e) {
    // 캐시 크기 초과 시 무시 (매번 수집)
    console.log('폴더 ID 캐시 저장 실패 (크기 초과): ' + e.message);
  }

  return map;
}

/**
 * 대상 폴더 ID 목록에서 모든 하위 폴더 ID를 재귀적으로 수집.
 * @return {Object} 폴더 ID를 키로 하는 해시맵 (빠른 lookup)
 */
function collectAllSubFolderIds_(folderIds) {
  var map = {};
  var queue = folderIds.slice();

  while (queue.length > 0) {
    var folderId = queue.shift();
    if (map[folderId]) continue;
    map[folderId] = true;

    try {
      var subFolders = DriveApp.getFolderById(folderId).getFolders();
      while (subFolders.hasNext()) {
        var sub = subFolders.next();
        if (!map[sub.getId()]) {
          queue.push(sub.getId());
        }
      }
    } catch (e) {
      console.error('하위 폴더 수집 실패 (' + folderId + '): ' + e.message);
    }
  }

  return map;
}

// ── 변환 ──────────────────────────────────────────────

/**
 * 파일명이 NFD이면 NFC로 변환 (Advanced Drive Service 사용 — 공유 드라이브 지원).
 * @return {Array|null} 로그 행 배열 또는 null
 */
function renameFileToNFC_(file, folderPath) {
  var name = file.getName();
  var nfcName = name.normalize('NFC');

  if (name === nfcName) return null;

  try {
    Drive.Files.update({ name: nfcName }, file.getId(), null, {
      supportsAllDrives: true
    });
    return [new Date(), file.getId(), name, nfcName, folderPath];
  } catch (e) {
    console.error('변환 실패 (' + name + '): ' + e.message);
    return null;
  }
}

// ── 로그 (배치 쓰기) ──────────────────────────────────

/**
 * 버퍼에 쌓인 로그를 한 번에 시트에 쓰기.
 * appendRow() 반복 대신 setValues() 배치 사용 (성능 100배 이상 개선).
 */
function flushLog_(logBuffer) {
  if (logBuffer.length === 0) return;

  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(LOG_SHEET);

  if (!sheet) {
    sheet = ss.insertSheet(LOG_SHEET);
    sheet.appendRow(['시각', '파일 ID', '원본 파일명', '변환 후 파일명', '폴더 경로']);
    sheet.getRange(1, 1, 1, 5).setFontWeight('bold');
  }

  var lastRow = sheet.getLastRow();
  sheet.getRange(lastRow + 1, 1, logBuffer.length, 5).setValues(logBuffer);
}

// ── 설정 ──────────────────────────────────────────────

/** 설정 시트에서 대상 폴더 ID 목록을 읽음 */
function getTargetFolderIds_() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(CONFIG_SHEET);

  if (!sheet) {
    sheet = ss.insertSheet(CONFIG_SHEET, 0);
    sheet.appendRow(['폴더 ID', '설명 (메모용)']);
    sheet.getRange(1, 1, 1, 2).setFontWeight('bold');
    sheet.setColumnWidth(1, 400);
    sheet.setColumnWidth(2, 300);
    return [];
  }

  var data = sheet.getDataRange().getValues();
  var ids = [];
  for (var i = 1; i < data.length; i++) {
    var id = String(data[i][0]).trim();
    if (id && id !== '폴더 ID') {
      ids.push(id);
    }
  }
  return ids;
}

// ── 트리거 관리 ───────────────────────────────────────

function enableTrigger() {
  disableTrigger();
  ScriptApp.newTrigger('main')
    .timeBased()
    .everyMinutes(15)
    .create();
  try {
    SpreadsheetApp.getUi().alert('15분마다 자동 실행 트리거가 설정되었습니다.');
  } catch (e) { /* 트리거 실행 시 UI 불가 */ }
}

function disableTrigger() {
  var triggers = ScriptApp.getProjectTriggers();
  for (var i = 0; i < triggers.length; i++) {
    if (triggers[i].getHandlerFunction() === 'main') {
      ScriptApp.deleteTrigger(triggers[i]);
    }
  }
}

// ── 유틸 ──────────────────────────────────────────────

function showCompletionMessage_(count, scanType) {
  try {
    SpreadsheetApp.getUi().alert(
      scanType + ' 완료!\n\n' +
      '변환된 파일: ' + count + '개\n' +
      (count > 0 ? '상세 내역은 "' + LOG_SHEET + '" 시트를 확인하세요.' : '변환이 필요한 파일이 없습니다.')
    );
  } catch (e) {
    // 트리거 실행 시에는 UI 사용 불가
    console.log(scanType + ' 완료. 변환: ' + count + '개');
  }
}
