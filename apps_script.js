/**
 * Google Apps Script for Persistent Bot Memory
 * 
 * 1. Open a new Google Sheet named "Sommelier Memory".
 * 2. In row 1, add these headers to columns A-D:
 *      A1: Chat ID
 *      B1: Active History
 *      C1: Long Term Summary
 *      D1: Last Updated
 * 3. Go to Extensions -> Apps Script.
 * 4. Paste this exact code, replacing everything.
 * 5. Click the "Deploy" button -> "New deployment".
 * 6. Select type: "Web app".
 * 7. Execute as: "Me"
 * 8. Who has access: "Anyone"
 * 9. Copy the deployed Web App URL!
 */

function doGet(e) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  var chatId = e.parameter.chat_id;
  
  if (!chatId) {
    return ContentService.createTextOutput(JSON.stringify({"error": "Missing chat_id"}))
      .setMimeType(ContentService.MimeType.JSON);
  }
  
  var data = sheet.getDataRange().getValues();
  // Find the row for this chat ID (skip header row 0)
  for (var i = 1; i < data.length; i++) {
    if (String(data[i][0]) === String(chatId)) {
      var activeHistoryRaw = data[i][1];
      // Safely parse history, default to empty array if corrupt
      var activeHistory = [];
      try {
         activeHistory = activeHistoryRaw ? JSON.parse(activeHistoryRaw) : [];
      } catch (err) {}
      
      return ContentService.createTextOutput(JSON.stringify({
        "chat_id": chatId,
        "active_history": activeHistory,
        "long_term_summary": data[i][2] || "",
        "updated_at": data[i][3] || 0
      })).setMimeType(ContentService.MimeType.JSON);
    }
  }
  
  // Not found
  return ContentService.createTextOutput(JSON.stringify({
    "chat_id": chatId,
    "active_history": [],
    "long_term_summary": "",
    "updated_at": 0
  })).setMimeType(ContentService.MimeType.JSON);
}

function doPost(e) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  
  try {
    var payload = JSON.parse(e.postData.contents);
    var chatId = String(payload.chat_id);
    var activeHistory = JSON.stringify(payload.active_history || []);
    var longTermSummary = payload.long_term_summary || "";
    var updatedAt = payload.updated_at || new Date().getTime() / 1000.0;
    
    var data = sheet.getDataRange().getValues();
    var rowIndex = -1;
    
    // Find the row
    for (var i = 1; i < data.length; i++) {
      if (String(data[i][0]) === chatId) {
        rowIndex = i + 1; // Google Sheets is 1-indexed
        break;
      }
    }
    
    if (rowIndex > -1) {
      // Update existing
      sheet.getRange(rowIndex, 2, 1, 3).setValues([[activeHistory, longTermSummary, updatedAt]]);
    } else {
      // Append new row
      sheet.appendRow([chatId, activeHistory, longTermSummary, updatedAt]);
    }
    
    return ContentService.createTextOutput(JSON.stringify({"status": "success"}))
      .setMimeType(ContentService.MimeType.JSON);
    
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({"error": err.toString()}))
      .setMimeType(ContentService.MimeType.JSON);
  }
}
