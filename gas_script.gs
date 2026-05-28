function doPost(e) {
  try {
    // リクエストからデータを取得
    var params = JSON.parse(e.postData.contents);
    var action = params.action; // 実行するアクション ('出勤' または '退勤')

    if (action === 'oha1') {
      // D列に「出勤」
      出勤時間を記入("出勤");
      return ContentService.createTextOutput(JSON.stringify({ status: 'success', message: '出勤(社内)を記入しました。' }))
        .setMimeType(ContentService.MimeType.JSON);

    } else if (action === 'oha2') {
      // D列に「在宅」
      出勤時間を記入("在宅");
      return ContentService.createTextOutput(JSON.stringify({ status: 'success', message: '出勤(在宅)を記入しました。' }))
        .setMimeType(ContentService.MimeType.JSON);

    } else if (action === 'otu') {
      退勤時間を記入();
      return ContentService.createTextOutput(JSON.stringify({ status: 'success', message: '退勤時間を記入しました。' }))
        .setMimeType(ContentService.MimeType.JSON);
    } else {
      return ContentService.createTextOutput(JSON.stringify({ status: 'error', message: '無効なアクションです。' }))
        .setMimeType(ContentService.MimeType.JSON);
    }
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({ status: 'error', message: error.message }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

function 出勤時間を記入(mode) {
  var sheet = getCurrentSheet();
  if (!sheet) {
    return;
  }

  var today = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'M/d');
  var lastRow = sheet.getLastRow();

  for (var i = 2; i <= lastRow; i++) {
    var dateCell = sheet.getRange(i, 2).getValue(); // B列の日付
    if (!(dateCell instanceof Date)) {
      continue;
    }

    var formattedDateCell = Utilities.formatDate(dateCell, Session.getScriptTimeZone(), 'M/d');

    if (formattedDateCell == today) {
      var currentTime = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'H:mm');
      // D列（4列目）に「出勤」または「在宅」
      sheet.getRange(i, 4).setValue(mode);
      sheet.getRange(i, 5).setValue(currentTime); // E列に出勤時間を記入
      break;
    }
  }
}

function 退勤時間を記入() {
  var sheet = getCurrentSheet();
  if (!sheet) {
    return;
  }

  var today = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'M/d');
  var lastRow = sheet.getLastRow();

  for (var i = 2; i <= lastRow; i++) {
    var dateCell = sheet.getRange(i, 2).getValue(); // B列の日付
    if (!(dateCell instanceof Date)) {
      continue;
    }

    var formattedDateCell = Utilities.formatDate(dateCell, Session.getScriptTimeZone(), 'M/d');

    if (formattedDateCell == today) {
      var currentTime = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'H:mm');
      sheet.getRange(i, 6).setValue(currentTime); // F列に退勤時間を記入
      sheet.getRange(i, 7).setValue('1:00'); // G列に休憩時間を記入
      break;
    }
  }
}

function getCurrentSheet() {
  var today = new Date();
  var year = today.getFullYear().toString().slice(2); // '24'
  var month = today.getMonth() + 1; // JavaScriptでは1月が0なので+1する
  var day = today.getDate();

  var sheetName;
  if (day > 15) {
    // 当月16日から翌月15日までの期間
    sheetName = year + '年' + (month + 1) + '月';
  } else {
    // 前月16日から当月15日までの期間
    sheetName = year + '年' + month + '月';
  }

  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(sheetName);

  if (!sheet) {
    SpreadsheetApp.getUi().alert(sheetName + " シートが見つかりません。");
    return null;
  }

  return sheet;
}
