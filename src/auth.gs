// auth.gs — Google Identity Services (GIS) authentication

/**
 * Google ID Token を検証してログイン/登録する。
 * クライアント側 GIS から受け取った idToken をサーバーで検証し、
 * ユーザー情報を返す。
 *
 * @param {string} idToken - Google Identity Services から取得した credential (JWT)
 * @return {Object} { ok, userKey, displayName, email, role } or { _error, message }
 */
function apiLoginWithGoogle(idToken) {
  try {
    if (!idToken) {
      return { _error: true, message: 'ID Tokenが指定されていません' };
    }

    // 1. Google tokeninfo API で ID Token を検証
    var url = 'https://oauth2.googleapis.com/tokeninfo?id_token=' + encodeURIComponent(idToken);
    var response = UrlFetchApp.fetch(url, { muteHttpExceptions: true });
    var code = response.getResponseCode();

    if (code !== 200) {
      return { _error: true, message: 'Google認証に失敗しました (HTTP ' + code + ')' };
    }

    var payload = JSON.parse(response.getContentText());

    // 2. email, name を取得
    var email = String(payload.email || '').trim().toLowerCase();
    var name = String(payload.name || payload.given_name || '').trim();

    if (!email) {
      return { _error: true, message: 'Googleアカウントからメールアドレスを取得できませんでした' };
    }

    // 3. Client ID の検証（ConfigシートのGOOGLE_CLIENT_IDとaud が一致するか確認）
    var config = getConfigMap_();
    var expectedClientId = getConfigValue_(config, 'GOOGLE_CLIENT_ID', '');
    if (expectedClientId && payload.aud !== expectedClientId) {
      return { _error: true, message: 'Client IDが一致しません' };
    }

    // 4. UserAccess でメール存在チェック（ホワイトリスト）
    var access = getUserAccessByEmail_(email);
    if (!access || !access.active) {
      return { _error: true, message: 'このアカウントは登録されていません。管理者にお問い合わせください。' };
    }
    var role = (access && access.role) ? access.role : 'user';

    // 5. UserAccess の displayName を優先（マスター名簿の氏名）
    var masterName = access.displayName || name || email.split('@')[0];

    // 6. Users シート登録/取得
    var user = ensureUser_(email, email, masterName);

    // 7. ユーザー情報を返す
    return {
      ok: true,
      userKey: user.userKey,
      displayName: masterName,
      email: email,
      role: role,
      authMethod: 'google'
    };
  } catch (e) {
    return { _error: true, message: 'Googleログインエラー: ' + String(e.message || e) };
  }
}

/**
 * ConfigシートからGoogle Client IDを取得する。
 * 値がない場合は空文字を返す（クライアント側でGoogleログインボタンを非表示にする）。
 *
 * @return {string} Google OAuth Client ID or ''
 */
function apiGetGoogleClientId() {
  try {
    var config = getConfigMap_();
    return getConfigValue_(config, 'GOOGLE_CLIENT_ID', '');
  } catch (e) {
    return '';
  }
}

// ============================================================
// OAuth 2.0 認可コードフロー（GIS 撤去に伴う新認証）
// ============================================================

function getAppExecUrl_() {
  var deployUrl = '';
  var configuredUrl = '';
  try {
    deployUrl = ScriptApp.getService().getUrl();
  } catch (deployErr) {}
  try {
    var config = getConfigMap_();
    configuredUrl = getConfigValue_(config, 'APP_EXEC_URL', '');
  } catch (configErr) {}

  if (deployUrl) {
    if (configuredUrl && configuredUrl !== deployUrl) {
      Logger.log('[APP_EXEC_URL_MISMATCH] config=' + configuredUrl + ' deploy=' + deployUrl);
    }
    return deployUrl;
  }

  return configuredUrl || '';
}

function getOAuthStartUrl_() {
  var config = getConfigMap_();
  var clientId = getConfigValue_(config, 'GOOGLE_CLIENT_ID', '');
  var redirectUri = getAppExecUrl_();
  var state = Utilities.getUuid();
  var nonce = Utilities.getUuid();
  var cache = CacheService.getScriptCache();
  cache.put('oauth_state_' + state, nonce, 300);
  return 'https://accounts.google.com/o/oauth2/v2/auth?'
    + 'client_id=' + encodeURIComponent(clientId)
    + '&redirect_uri=' + encodeURIComponent(redirectUri)
    + '&response_type=code'
    + '&scope=' + encodeURIComponent('openid email profile')
    + '&state=' + encodeURIComponent(state)
    + '&nonce=' + encodeURIComponent(nonce)
    + '&prompt=select_account';
}

function generateOAuthStartPage_() {
  var authUrl = getOAuthStartUrl_();
  var execUrl = getAppExecUrl_();
  var html =
    '<!DOCTYPE html><html><head><meta charset="utf-8">' +
    '<meta name="viewport" content="width=device-width,initial-scale=1">' +
    '<title>ログイン</title></head>' +
    '<body style="display:flex;justify-content:center;align-items:center;' +
    'min-height:80vh;font-family:sans-serif;margin:0;padding:16px">' +
    '<div style="text-align:center;max-width:400px">' +
      '<div style="font-size:2.5rem;margin-bottom:16px">\uD83D\uDD10</div>' +
      '<div style="font-size:1.1rem;font-weight:700;margin-bottom:8px">' +
        'Googleアカウントでログイン</div>' +
      '<div style="font-size:0.85rem;color:#666;margin-bottom:24px;line-height:1.5">' +
        'Googleのログイン画面に移動します。</div>' +
      '<a target="_top" href="' + authUrl + '" ' +
        'style="display:inline-flex;align-items:center;gap:8px;padding:10px 24px;' +
        'border:1px solid #dadce0;border-radius:4px;background:#fff;font-size:14px;' +
        'cursor:pointer;font-family:Roboto,sans-serif;text-decoration:none;color:#3c4043">' +
        '<img src="https://developers.google.com/identity/images/g-logo.png" ' +
        'width="18" height="18" alt="">Googleアカウントに進む</a>' +
      '<div style="margin-top:16px">' +
        '<a href="' + execUrl + '" target="_top" ' +
          'style="color:#2563eb;font-size:0.8rem;text-decoration:none">\u623B\u308B</a>' +
      '</div>' +
    '</div></body></html>';
  return HtmlService.createHtmlOutput(html)
    .setTitle('ログイン')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

function logOAuthError_(step, detail) {
  try {
    var db = getDb_();
    var sh = db.getSheetByName('AuthLog');
    if (!sh) {
      sh = db.insertSheet('AuthLog');
      sh.appendRow(['timestamp', 'step', 'detail']);
    }
    sh.appendRow([new Date().toISOString(), step, String(detail).substring(0, 500)]);
  } catch (e) { Logger.log('[AUTH_LOG_ERROR] ' + e); }
}

function handleManualLogin_(email) {
  var access = getUserAccessByEmail_(email);
  if (!access || !access.active) {
    return errorPage_('このアカウントは登録されていません: ' + email);
  }
  var user = ensureUser_(email, email, access.displayName || email.split('@')[0]);
  var template = HtmlService.createTemplateFromFile('index');
  template.serverAuthResult = JSON.stringify({
    userKey: user.userKey,
    displayName: access.displayName || user.displayName,
    email: email,
    role: access.role || 'user'
  }).replace(/</g, String.fromCharCode(92) + 'u003c');
  template.appExecUrl = getAppExecUrl_();
  return template.evaluate()
    .setTitle(APP_TITLE_)
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL)
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

function handleOAuthCallback_(code, state) {
  try {
    var cache = CacheService.getScriptCache();
    var expectedNonce = cache.get('oauth_state_' + state);
    if (!expectedNonce) {
      // state消費済みフラグがある場合のみフォールバック（リロード想定）
      // フラグがなければ不正/期限切れリクエストとして拒否（CSRF防御維持）
      var wasDone = cache.get('oauth_done_' + state);
      if (wasDone) {
        logOAuthError_('state_consumed', 'reload after success: ' + state);
        var template = HtmlService.createTemplateFromFile('index');
        template.serverAuthResult = '';
        template.appExecUrl = getAppExecUrl_();
        return template.evaluate()
          .setTitle(APP_TITLE_)
          .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL)
          .addMetaTag('viewport', 'width=device-width, initial-scale=1');
      }
      logOAuthError_('state_invalid', 'state not found in cache: ' + state);
      return errorPage_('認証エラー: リクエストが無効または期限切れです');
    }
    cache.remove('oauth_state_' + state);

    var config = getConfigMap_();
    var clientId = getConfigValue_(config, 'GOOGLE_CLIENT_ID', '');
    var clientSecret = PropertiesService.getScriptProperties().getProperty('GOOGLE_CLIENT_SECRET');
    var redirectUri = getAppExecUrl_();

    logOAuthError_('token_request', 'clientId=' + (clientId ? clientId.substring(0,20) + '...' : 'EMPTY') + ' redirectUri=' + redirectUri);

    var tokenResp = UrlFetchApp.fetch('https://oauth2.googleapis.com/token', {
      method: 'post',
      payload: {
        code: code,
        client_id: clientId,
        client_secret: clientSecret,
        redirect_uri: redirectUri,
        grant_type: 'authorization_code'
      },
      muteHttpExceptions: true
    });
    if (tokenResp.getResponseCode() !== 200) {
      logOAuthError_('token_exchange', 'HTTP ' + tokenResp.getResponseCode() + ': ' + tokenResp.getContentText());
      return errorPage_('トークン取得に失敗しました (HTTP ' + tokenResp.getResponseCode() + ')');
    }

    var tokens = JSON.parse(tokenResp.getContentText());
    var loginResult = apiLoginWithGoogle(tokens.id_token);
    if (!loginResult || loginResult._error) {
      logOAuthError_('login', loginResult ? loginResult.message : 'null result');
      return errorPage_(loginResult ? loginResult.message : '認証エラー');
    }

    var idPayload = JSON.parse(
      Utilities.newBlob(
        Utilities.base64DecodeWebSafe(tokens.id_token.split('.')[1])
      ).getDataAsString()
    );
    if (idPayload.nonce !== expectedNonce) {
      logOAuthError_('nonce_check', 'expected=' + expectedNonce + ' got=' + idPayload.nonce);
      return errorPage_('認証エラー: nonce が一致しません');
    }
    logOAuthError_('success', 'email=' + (loginResult.email || ''));
    // リロード時のフォールバック用にstate消費済みフラグを残す（5分間）
    cache.put('oauth_done_' + state, '1', 300);

    if (idPayload.sub) {
      saveGoogleSub_(loginResult.userKey, idPayload.sub);
    }

    var template = HtmlService.createTemplateFromFile('index');
    template.serverAuthResult = JSON.stringify({
      userKey: loginResult.userKey,
      displayName: loginResult.displayName,
      email: loginResult.email,
      role: loginResult.role
    }).replace(/</g, String.fromCharCode(92) + 'u003c');
    template.appExecUrl = getAppExecUrl_();
    return template.evaluate()
      .setTitle(APP_TITLE_)
      .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL)
      .addMetaTag('viewport', 'width=device-width, initial-scale=1');
  } catch (e) {
    logOAuthError_('callback_error', String(e.message || e));
    return errorPage_('認証処理中にエラーが発生しました。しばらくしてから再度お試しください。');
  }
}

function errorPage_(message) {
  var url = getAppExecUrl_();
  var safe = String(message || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  return HtmlService.createHtmlOutput(
    '<p>' + safe + '</p><p><a href="' + url + '" target="_top">トップへ戻る</a></p>'
  ).setTitle('認証エラー');
}

function saveGoogleSub_(userKey, sub) {
  try {
    var sh = getSheet_(SHEETS.Users);
    var headers = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0];
    var colIndex = -1;
    for (var i = 0; i < headers.length; i++) {
      if (String(headers[i]).trim().toLowerCase() === 'googlesub') { colIndex = i; break; }
    }
    if (colIndex < 0) {
      sh.getRange(1, sh.getLastColumn() + 1).setValue('googleSub');
      colIndex = sh.getLastColumn() - 1;
    }
    var data = sh.getDataRange().getValues();
    var ukCol = -1;
    for (var j = 0; j < headers.length; j++) {
      if (String(headers[j]).trim().toLowerCase() === 'userkey') { ukCol = j; break; }
    }
    if (ukCol < 0) return;
    for (var r = 1; r < data.length; r++) {
      if (String(data[r][ukCol]) === userKey && !String(data[r][colIndex] || '').trim()) {
        sh.getRange(r + 1, colIndex + 1).setValue(sub);
        break;
      }
    }
  } catch (e) {
    Logger.log('[SAVE_GOOGLE_SUB_ERROR] ' + String(e.message || e));
  }
}

/**
 * OAuth設定診断エンドポイント
 * doGet で ?diag=oauth を検出して呼び出す
 * 秘密情報の値は表示しない（存在有無のみ）
 */
function diagOAuth_() {
  var config = getCachedConfig_();
  var props = PropertiesService.getScriptProperties();

  var clientId = getConfigValue_(config, 'GOOGLE_CLIENT_ID', '');
  var clientSecret = props.getProperty('GOOGLE_CLIENT_SECRET');
  var appExecUrl = getConfigValue_(config, 'APP_EXEC_URL', '');
  var resolvedAppExecUrl = getAppExecUrl_();
  var dbId = props.getProperty('DB_SPREADSHEET_ID');

  var results = {
    timestamp: new Date().toISOString(),
    app: APP_NAME_,
    checks: {
      GOOGLE_CLIENT_ID: clientId ? 'SET (' + clientId.substring(0, 12) + '...)' : 'MISSING',
      GOOGLE_CLIENT_SECRET: clientSecret ? 'SET (' + clientSecret.length + ' chars)' : 'MISSING',
      APP_EXEC_URL: appExecUrl || 'MISSING',
      RESOLVED_APP_EXEC_URL: resolvedAppExecUrl || 'MISSING',
      DB_SPREADSHEET_ID: dbId ? 'SET (' + dbId.substring(0, 12) + '...)' : 'MISSING',
      FALLBACK_DB_ID: (typeof FALLBACK_DB_ID_ !== 'undefined' && FALLBACK_DB_ID_) ? 'SET' : 'MISSING/EMPTY'
    },
    validation: {}
  };

  // APP_EXEC_URL とデプロイURLの一致チェック
  var deployUrl = ScriptApp.getService().getUrl();
  results.checks.DEPLOY_URL = deployUrl || 'UNKNOWN';
  if (appExecUrl && deployUrl) {
    results.validation.URL_MATCH = (appExecUrl === deployUrl) ? 'OK' : 'MISMATCH: APP_EXEC_URL=' + appExecUrl + ' vs DEPLOY=' + deployUrl;
  }
  if (resolvedAppExecUrl && deployUrl) {
    results.validation.RESOLVED_URL_MATCH = (resolvedAppExecUrl === deployUrl) ? 'OK' : 'MISMATCH: RESOLVED=' + resolvedAppExecUrl + ' vs DEPLOY=' + deployUrl;
  }

  // Client IDのフォーマットチェック
  if (clientId) {
    results.validation.CLIENT_ID_FORMAT = clientId.endsWith('.apps.googleusercontent.com') ? 'OK' : 'INVALID FORMAT';
  }

  // AuthLog 最新10件
  try {
    var db = getDb_();
    var authLogSh = db.getSheetByName('AuthLog');
    if (authLogSh && authLogSh.getLastRow() > 1) {
      var lastRow = authLogSh.getLastRow();
      var startRow = Math.max(2, lastRow - 9);
      var numRows = lastRow - startRow + 1;
      var logData = authLogSh.getRange(startRow, 1, numRows, 3).getValues();
      results.authLog = logData.map(function(r) {
        return { timestamp: String(r[0]), step: String(r[1]), detail: String(r[2]) };
      }).reverse();
    }
  } catch(e) { results.authLogError = String(e); }

  // getUserContext_ デバッグ
  try {
    var sessionEmail = '';
    try { sessionEmail = Session.getActiveUser().getEmail() || ''; } catch(se) {}
    results.userContextDebug = {
      sessionEmail: sessionEmail || '(empty)',
      clientUserKeySet: !!(__clientUserKey),
      note: 'apiGetHome未経由のため__clientUserKeyは空'
    };
  } catch(e) {}

  return HtmlService.createHtmlOutput('<pre>' + JSON.stringify(results, null, 2) + '</pre>')
    .setTitle('OAuth Diagnostics')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}
