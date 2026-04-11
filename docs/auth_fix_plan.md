# eラーニング認証フロー修正計画書

**作成日**: 2026-03-17
**対象**: 建築(archi-16w-training) / 土木(doboku-14w-training) の2アプリ
**目的**: 一部PCでログインできない不具合の根本修正

---

## 1. 不具合の症状

| アプリ | 症状 | 影響人数 |
|--------|------|----------|
| 建築 | 「Googleでログイン」ボタンを押しても反応しない | 6名+ |
| 土木 | ページ表示時に「エラーが発生しました」と表示 | 6名+ |

**共通**: ログインせずにURLへアクセスするとエラー → その後ログインしても画面が開けない

---

## 2. 原因分析

### 2.1 根本原因: `google.accounts.id.prompt()` 依存

両アプリとも、ログインボタンのクリック時に **One Tap UI** (`google.accounts.id.prompt()`) を呼び出す実装。

```javascript
// 建築: src/index.html:1029 / 土木: src/index.html:1163
google.accounts.id.prompt(function(notification) {
  if (notification.isNotDisplayed()) {
    var reason = notification.getNotDisplayedReason();
    // → alertを出すだけで、代替手段なし
  }
});
```

**`prompt()` が失敗する条件**（Google公式ドキュメント）:
- 3rd-party cookie がブロックされている（Chrome 2024年以降デフォルト）
- FedCM（Federated Credential Management）がブラウザで無効
- Google アカウントのセッションが切れている / 未ログイン
- Chrome のプライバシー設定が厳しい（企業ポリシー含む）
- Edge で Google アカウント未連携
- ポップアップブロッカーの影響

**結果**: `prompt()` が表示されないと、ユーザーは何もできない。alertが出ることもあるが、回避手段がない。

### 2.2 起動フローの問題: 未認証でも API を叩く

```
DOMContentLoaded
  └→ loadHome()                    ← 即座に実行
      ├→ getHomeCacheFromStorage_()  ← localStorage に壊れたキャッシュがある場合も
      └→ apiGetHome(getClientUserKey())  ← userKey が空でもサーバーへ送信
          └→ サーバー: getUserContext_()
              └→ authMethod: 'none' → needsRegistration: true を返す
```

**問題点**:
- `loadHome()` が無条件に `apiGetHome()` を呼ぶ
- `apiGetHome()` の失敗時（GASの実行エラーなど）、`handleApiError_()` が `isLoginError_()` をチェック
- `isLoginError_()` は文字列マッチで判定するため、GASのランタイムエラー（`ScriptError`）も認証エラーと誤判定する
- 誤判定でログイン画面に飛ばされるが、`prompt()` が動かないPCでは詰む

**関連コード**:
- 建築: [src/index.html:1119](src/index.html#L1119) (`loadHome`)
- 土木: [src/index.html:1259](src/index.html#L1259) (`loadHome`)

### 2.3 サーバー側の認証優先度の問題

```javascript
// 建築・土木 共通: src/logic.gs:102
function getUserContext_() {
  var email = getActiveEmail_();  // Priority 1: Session.getActiveUser().getEmail()

  if (email) {
    // Google Workspace ユーザーの場合 → Session認証
    return { userKey: email, authMethod: 'google' };
  }

  var cuk = __clientUserKey || '';  // Priority 2: client localStorage の userKey
  if (cuk) {
    var existing = findUserByKey_(cuk);
    if (existing) {
      return { userKey: existing.userKey, authMethod: 'google_local' };
    }
  }

  return { userKey: '', authMethod: 'none' };  // Priority 3: 未認証
}
```

**問題点**:
- `Session.getActiveUser().getEmail()` は GAS Web アプリの実行モードが `USER_ACCESSING` の場合のみ有効
- 現在の `appsscript.json` には `webapp` セクションがない（GASコンソール上でのデプロイ設定に依存）
- ドキュメント（`docs/user_admin_guide.md:11`）は `USER_ACCESSING` 前提で書かれている
- 実際のデプロイが `USER_DEPLOYING` の場合、`Session.getActiveUser()` は常に空を返す
- その場合、Priority 2 の `__clientUserKey`（= GIS ログインで localStorage に保存した値）のみが認証手段
- つまり **GIS ログインが唯一の認証経路** だが、`prompt()` が壊れると全て詰む

### 2.4 「一度エラーが出ると復帰できない」問題

エラー発生後の復帰パスがない:
1. 未ログインでアクセス → `apiGetHome()` が `needsRegistration: true` を返す → ログイン画面表示
2. ログイン画面で `prompt()` が無反応 → ユーザー操作不能
3. `localStorage` に壊れた `userKey` が残っている場合 → `findUserByKey_()` が null → `authMethod: 'none'` → 再びログイン画面 → 無限ループ

**localStorage をクリアする UI もない**（DevToolsを開ける利用者でない限り復帰不能）

---

## 3. 修正方針

### 方針: GIS-only 認証に統一 + `prompt()` 依存をやめる

**理由**:
- 利用者は `@gmail.com` アカウント（Google Workspace ではない）
- `Session.getActiveUser()` は gmail.com ユーザーでは動作しない（`USER_ACCESSING` でも）
- 現行コードも実質 GIS に依存しており、Session 認証は dead code に近い
- GIS の **`renderButton()`** を使えば、`prompt()` の FedCM/cookie 依存を回避できる

---

## 4. 修正タスク詳細

### Task 1: ログイン UI の変更（クライアント側）

**対象ファイル**: 建築 `src/index.html` / 土木 `src/index.html`

#### 1-1. `showRegistrationScreen_()` を書き換え

**現状** (土木 line 1087 / 建築 line 965):
```javascript
function showRegistrationScreen_() {
  var html = '...<button id="google-signin-btn" onclick="triggerGoogleSignIn_()"...>Google でログイン</button>...';
  setHtml('home-summary', html);
  initGoogleSignIn_();
}
```

**修正後**:
```javascript
function showRegistrationScreen_() {
  var html =
    '<div style="text-align:center;padding:32px 16px">' +
      '<div style="font-size:2.5rem;margin-bottom:16px">📝</div>' +
      '<div style="font-size:1.1rem;font-weight:700;margin-bottom:8px">ログインしてください</div>' +
      '<div style="font-size:0.85rem;color:#6b7280;margin-bottom:20px;line-height:1.5">' +
        '学習履歴を記録するためにGoogleアカウントでログインしてください。' +
      '</div>' +
      // Google公式ボタンを描画するコンテナ
      '<div id="g_id_signin" style="display:flex;justify-content:center;margin-bottom:16px"></div>' +
      // フォールバック: 公式ボタンが描画できない場合のカスタムボタン
      '<div id="google-signin-fallback" style="max-width:300px;margin:0 auto;display:none">' +
        '<button id="google-signin-btn" onclick="triggerGoogleSignIn_()" ...>Google でログイン</button>' +
      '</div>' +
      // 手動リカバリーリンク
      '<div style="margin-top:16px">' +
        '<a href="#" onclick="resetClientAuth_();return false" style="font-size:0.75rem;color:#9ca3af">ログインに問題がある場合はこちら</a>' +
      '</div>' +
    '</div>';
  setHtml('home-summary', html);
  // 子要素をクリアする処理は現状通り
  ['home-next-action','home-kpi',...].forEach(function(id){...});
  initGoogleSignIn_();
}
```

#### 1-2. `initGoogleSignIn_()` を変更: `renderButton()` を追加

**現状** (土木 line 1119 / 建築 line 993):
```javascript
function initGoogleSignIn_() {
  if (__googleClientId) {
    showGoogleButton_(__googleClientId);
    return;
  }
  google.script.run
    .withSuccessHandler(function(clientId) {
      __googleClientId = clientId || '';
      if (__googleClientId) showGoogleButton_(__googleClientId);
    })
    .apiGetGoogleClientId();
}
```

**修正後**:
```javascript
function initGoogleSignIn_() {
  if (__googleClientId) {
    showGoogleButton_(__googleClientId);
    return;
  }
  google.script.run
    .withSuccessHandler(function(clientId) {
      __googleClientId = clientId || '';
      if (__googleClientId) {
        showGoogleButton_(__googleClientId);
      } else {
        // Client ID未設定 → フォールバックボタンも隠す
        showAlert('ログイン設定が完了していません。管理者にお問い合わせください。');
      }
    })
    .withFailureHandler(function() {
      showAlert('ログイン設定の取得に失敗しました。ページを再読み込みしてください。');
    })
    .apiGetGoogleClientId();
}
```

#### 1-3. `showGoogleButton_()` を変更: `renderButton()` を追加

**現状** (土木 line 1139 / 建築 line 1009):
```javascript
function showGoogleButton_(clientId) {
  if (!__googleInitialized && google.accounts && google.accounts.id) {
    google.accounts.id.initialize({
      client_id: clientId,
      callback: handleGoogleCredential_,
      auto_select: false
    });
    __googleInitialized = true;
  }
}
```

**修正後**:
```javascript
function showGoogleButton_(clientId) {
  if (typeof google === 'undefined' || !google.accounts || !google.accounts.id) {
    // GIS ライブラリ未読み込み → フォールバックボタンを表示
    var fb = document.getElementById('google-signin-fallback');
    if (fb) fb.style.display = 'block';
    return;
  }

  if (!__googleInitialized) {
    google.accounts.id.initialize({
      client_id: clientId,
      callback: handleGoogleCredential_,
      auto_select: false,
      use_fedcm_for_prompt: true  // FedCM を明示的に有効化
    });
    __googleInitialized = true;
  }

  // Google公式ボタンを描画（prompt() 不要で確実に表示される）
  var container = document.getElementById('g_id_signin');
  if (container) {
    google.accounts.id.renderButton(container, {
      type: 'standard',
      theme: 'outline',
      size: 'large',
      text: 'signin_with',
      shape: 'rectangular',
      logo_alignment: 'left',
      width: 300
    });
  }
}
```

**`renderButton()` のメリット**:
- `prompt()` と異なり、3rd-party cookie / FedCM の状態に関係なく **常にボタンが描画される**
- ユーザーがボタンをクリックすると Google の標準ポップアップが開く
- ポップアップ方式のため、ブラウザ設定の影響を受けにくい
- `callback` は `initialize()` で設定済みなので、`handleGoogleCredential_()` がそのまま呼ばれる

#### 1-4. `triggerGoogleSignIn_()` はフォールバック用に残す

**修正後**:
```javascript
function triggerGoogleSignIn_() {
  if (!__googleClientId) {
    showAlert('Google Client IDが設定されていません。管理者にお問い合わせください。');
    return;
  }
  if (typeof google === 'undefined' || !google.accounts || !google.accounts.id) {
    showAlert('Google Sign-Inの読み込みに失敗しました。ページを再読み込みしてください。');
    return;
  }
  // popup fallback: prompt() の代わりに OAuth2 popup を開く方法も検討可能
  // ただし renderButton() が使える環境なら不要
  google.accounts.id.prompt(function(notification) {
    if (notification.isNotDisplayed()) {
      var reason = notification.getNotDisplayedReason();
      showAlert('Google Sign-Inを表示できませんでした (' + reason + ')。' +
                '上のGoogleボタンをクリックしてログインしてください。');
    }
  });
}
```

### Task 2: 起動フローの変更（クライアント側）

**対象ファイル**: 建築 `src/index.html` / 土木 `src/index.html`

#### 2-1. `DOMContentLoaded` のエントリポイント変更

**現状** (土木 line 4141 / 建築 line 3594):
```javascript
document.addEventListener('DOMContentLoaded', loadHome);
```

**修正後**:
```javascript
document.addEventListener('DOMContentLoaded', bootApp_);
```

#### 2-2. `bootApp_()` を新設

```javascript
function bootApp_() {
  var userKey = getClientUserKey();
  if (!userKey) {
    // userKey がない = 未ログイン → ログイン画面を即表示（APIは叩かない）
    showRegistrationScreen_();
    return;
  }
  // userKey がある = 過去にログイン済み → 通常のホーム読み込み
  loadHome();
}
```

**効果**:
- 未ログイン時に `apiGetHome()` を叩かないため、GASのコールドスタート待ちやランタイムエラーを回避
- 「ログイン前にアクセス → エラー → ログインしても開けない」の問題を解消
- ログイン画面の表示が高速化（サーバー通信なし）

#### 2-3. `loadHome()` 内のエラーハンドリング強化

**現状** (土木 line 1290 / 建築 line 1150):
```javascript
.withFailureHandler(function(err){
  hideLoading();
  var result = handleApiError_(err, 'データ取得に失敗しました');
  if (result === true) return;
  if (!cached) {
    setHtml('home-summary', '<div class="danger">' + escapeHtml(result) + '</div>');
  }
})
```

**修正後**:
```javascript
.withFailureHandler(function(err){
  hideLoading();
  console.error('apiGetHome FAIL:', err);
  var result = handleApiError_(err, 'データ取得に失敗しました');
  if (result === true) return;  // ログインエラー → ログイン画面へ
  if (!cached) {
    // エラー表示 + 再試行ボタン + リセットリンク
    setHtml('home-summary',
      '<div class="danger">' + escapeHtml(result) + '</div>' +
      '<div style="text-align:center;margin-top:16px">' +
        '<button onclick="loadHome()" style="padding:8px 24px;border-radius:6px;border:1px solid #ccc;cursor:pointer">再読み込み</button>' +
        ' <a href="#" onclick="resetClientAuth_();return false" style="font-size:0.8rem;color:#9ca3af;margin-left:12px">ログインし直す</a>' +
      '</div>'
    );
  }
})
```

### Task 3: 認証リセット機能の追加（クライアント側）

**対象ファイル**: 建築 `src/index.html` / 土木 `src/index.html`

#### 3-1. `resetClientAuth_()` を新設

```javascript
function resetClientAuth_() {
  try {
    // 土木の場合
    localStorage.removeItem('doboku14w_userKey');
    localStorage.removeItem('doboku14w_homeCache');
    // 建築の場合
    // localStorage.removeItem('archi16w_userKey');
    // localStorage.removeItem('archi16w_homeCache');
  } catch(e) {}

  // GIS の状態もリセット
  __googleInitialized = false;
  __googleClientId = '';

  // ログイン画面を再表示
  showRegistrationScreen_();
}
```

**効果**:
- 壊れた localStorage を UI からクリアできる
- DevTools を開かなくても復帰可能

### Task 4: サーバー側の変更

**対象ファイル**: 建築・土木 共通の `src/logic.gs`, `src/api.gs`, `src/auth.gs`

#### 4-1. `getUserContext_()` の優先度変更

**現状** (logic.gs:102):
```javascript
function getUserContext_() {
  var email = getActiveEmail_();       // Priority 1: Session
  if (email) { ... return; }
  var cuk = __clientUserKey || '';      // Priority 2: clientUserKey
  if (cuk) { ... return; }
  return { authMethod: 'none' };       // Priority 3: 未認証
}
```

**修正後**:
```javascript
function getUserContext_() {
  // Priority 1: Client-provided userKey from GIS login (localStorage)
  var cuk = __clientUserKey || '';
  if (cuk) {
    var existing = findUserByKey_(cuk);
    if (existing) {
      return {
        userKey: existing.userKey,
        email: existing.email || '',
        displayName: existing.displayName,
        authMethod: 'google_local'
      };
    }
    // userKey が渡されたが Users に見つからない → 認証無効
    // (壊れた userKey の場合はここに来る)
  }

  // Priority 2: Google Workspace Session (補助)
  var email = getActiveEmail_();
  if (email) {
    var profile = getDirectoryProfile_(email);
    return {
      userKey: email,
      email: profile.email,
      displayName: profile.displayName,
      authMethod: 'google'
    };
  }

  // Priority 3: 未認証
  return { userKey: '', email: '', displayName: '', authMethod: 'none' };
}
```

**理由**:
- gmail.com ユーザーでは `Session.getActiveUser().getEmail()` が常に空
- `__clientUserKey` を優先することで、GIS ログイン済みユーザーを確実に認識
- Session 認証は将来の Google Workspace ユーザー対応用に残す

#### 4-2. `apiGetHome()` の早期リターン明確化

**現状** (api.gs:20):
```javascript
function apiGetHome(clientUserKey) {
  __clientUserKey = clientUserKey || '';
  try {
    var config = getConfigMap_();
    var userCtx = getUserContext_();
    if (userCtx.authMethod === 'none') {
      return { needsRegistration: true, config: config };
    }
    var access = requireActiveUser_(userCtx);  // ← ここで例外が飛ぶ可能性
    ...
```

**修正後**:
```javascript
function apiGetHome(clientUserKey) {
  __clientUserKey = clientUserKey || '';
  try {
    var config = getConfigMap_();
    var userCtx = getUserContext_();

    // 未認証 → 軽量レスポンスで即リターン（重い処理に入らない）
    if (userCtx.authMethod === 'none') {
      return { needsRegistration: true, config: { GOOGLE_CLIENT_ID: getConfigValue_(config, 'GOOGLE_CLIENT_ID', '') } };
    }

    var access = requireActiveUser_(userCtx);
    var user = ensureUser_(userCtx.userKey, userCtx.email, userCtx.displayName);
    // ... 以降は現状通り
```

**変更点**:
- `needsRegistration: true` の場合に `config` 全体ではなく `GOOGLE_CLIENT_ID` のみ返す（不要な情報を減らす）
- ただしこれは任意の最適化。既存の動作にも問題なし。

#### 4-3. `apiLoginWithGoogle()` のエラーコード追加

**現状** (auth.gs:11):
```javascript
return { _error: true, message: 'このアカウントは登録されていません。管理者にお問い合わせください。' };
```

**修正後**:
```javascript
return { _error: true, errorCode: 'AUTH_NOT_REGISTERED', message: 'このアカウントは登録されていません。管理者にお問い合わせください。' };
```

**全エラーコード一覧**:

| errorCode | 発生箇所 | 意味 |
|-----------|----------|------|
| `AUTH_NO_TOKEN` | auth.gs:14 | idToken 未指定 |
| `AUTH_GOOGLE_FAIL` | auth.gs:23 | Google tokeninfo API 失敗 |
| `AUTH_NO_EMAIL` | auth.gs:33 | メール取得不可 |
| `AUTH_CLIENT_MISMATCH` | auth.gs:40 | Client ID 不一致 |
| `AUTH_NOT_REGISTERED` | auth.gs:46 | UserAccess 未登録/無効 |
| `AUTH_INTERNAL` | auth.gs:66 | 予期せぬエラー |

**クライアント側で使用**:
```javascript
// handleGoogleCredential_ 内
if (res._error && res.errorCode === 'AUTH_NOT_REGISTERED') {
  showAlert(res.message);
  // ログイン画面に留まる（resetは不要）
} else if (res._error) {
  showAlert(res.message);
  resetClientAuth_();  // 状態リセットして再試行可能に
}
```

### Task 5: ドキュメント修正

**対象ファイル**: 建築・土木 共通 `docs/user_admin_guide.md`

**修正箇所** (line 11):
```markdown
// 現状
3. Webアプリの実行ユーザーは `USER_ACCESSING` で動作

// 修正後
3. Webアプリの実行ユーザーは `USER_DEPLOYING` で動作（gmail.comユーザー対応のため）
4. 認証方式は Google Identity Services (GIS) によるクライアント側ログインを使用
```

---

## 5. 実装対象ファイル一覧

| # | ファイル | 変更内容 | 建築 | 土木 |
|---|---------|---------|------|------|
| 1 | `src/index.html` | showRegistrationScreen_, initGoogleSignIn_, showGoogleButton_, triggerGoogleSignIn_, bootApp_, resetClientAuth_, loadHome エラーハンドリング, DOMContentLoaded | ✅ | ✅ |
| 2 | `src/logic.gs` | getUserContext_ の優先度変更 | ✅ | ✅ |
| 3 | `src/api.gs` | apiGetHome の早期リターン最適化（任意） | ✅ | ✅ |
| 4 | `src/auth.gs` | errorCode 追加 | ✅ | ✅ |
| 5 | `docs/user_admin_guide.md` | USER_ACCESSING → USER_DEPLOYING 記述修正 | ✅ | ✅ |

---

## 6. 変更の影響範囲

### 非破壊的な変更（既存動作を壊さない）
- `renderButton()` の追加: 既存の `initialize()` + `callback` はそのまま使える
- `bootApp_()` の追加: `loadHome()` は内部ロジック不変
- `resetClientAuth_()` の追加: 新機能の追加のみ
- `errorCode` の追加: 既存の `_error` + `message` に追加フィールド

### 注意が必要な変更
- `getUserContext_()` の優先度変更: **Session → clientUserKey** から **clientUserKey → Session** に変更
  - 影響: Google Workspace ユーザーで `__clientUserKey` が空の場合、Session から取得（現状通り）
  - 影響: `__clientUserKey` が渡された場合、Session より優先（動作改善）
  - **リスク低**: gmail.com ユーザーでは Session が常に空なので、実質的に変わらない

---

## 7. テスト計画

### 7.1 手動テスト項目

| # | シナリオ | 期待結果 | 建築 | 土木 |
|---|---------|---------|------|------|
| 1 | 新規PC、localStorage空、Google未ログインでURLを開く | ログイン画面が表示される（エラーなし） | ✅ | ✅ |
| 2 | Google公式ボタンをクリック | ポップアップが開き、Googleアカウント選択画面が表示される | ✅ | ✅ |
| 3 | Googleアカウントでログイン完了 | ホーム画面が表示される | ✅ | ✅ |
| 4 | ログイン済みの状態でURLを再度開く | キャッシュからホーム画面が即表示される | ✅ | ✅ |
| 5 | 「ログインに問題がある場合はこちら」をクリック | localStorageクリア → ログイン画面に戻る | ✅ | ✅ |
| 6 | 壊れたuserKeyがlocalStorageに残っている状態 | ログイン画面にフォールバック | ✅ | ✅ |
| 7 | 3rd-party cookie制限あり（Chromeシークレット等） | renderButton()でボタンが表示される | ✅ | ✅ |
| 8 | Chrome で動作確認 | 正常 | ✅ | ✅ |
| 9 | Edge で動作確認 | 正常 | ✅ | ✅ |
| 10 | a.furukawa.tscg@gmail.com で初回ログイン | Users行が自動作成される | ✅ | ✅ |
| 11 | UserAccess未登録のメールでログイン | 「登録されていません」エラー | ✅ | ✅ |
| 12 | テスト実行中にセッション切れ | エラー表示 + 再ログイン導線 | ✅ | ✅ |

### 7.2 自動テスト（GAS内診断）

```
GET /exec?action=checkUserAccess&email=a.furukawa.tscg@gmail.com
→ { found: true, active: true } を確認
```

---

## 8. デプロイ手順

1. **建築アプリから先に修正**（影響範囲が小さい方から）
2. `clasp push` でコードをアップロード
3. GASエディタで「デプロイを管理」→ 新しいバージョンを作成
4. テスト項目を実行
5. 問題なければ **土木アプリも同様に修正**
6. 古川さん + 他5名に確認依頼

---

## 9. 他AIへの相談ポイント

以下の設計判断について、妥当性を確認してください:

### Q1: `renderButton()` への移行は妥当か？
- `prompt()` (One Tap) をやめて `renderButton()` (標準ボタン) に移行
- `prompt()` はFedCM/cookie依存で失敗しやすい
- `renderButton()` は確実に描画される
- **トレードオフ**: One Tap の UX（ワンクリックログイン）は失われる

### Q2: 起動フローの変更は妥当か？
- `DOMContentLoaded → loadHome() → apiGetHome()` を
- `DOMContentLoaded → bootApp_() → userKeyチェック → apiGetHome() or showRegistration()` に変更
- 未認証時にサーバー通信を完全にスキップ
- **懸念**: `apiGetHome()` の `needsRegistration` レスポンスに依存している処理がないか

### Q3: `getUserContext_()` の優先度変更は妥当か？
- Session.getActiveUser() 優先 → __clientUserKey 優先 に変更
- gmail.com ユーザーでは Session が常に空なので実質影響なし
- **懸念**: 将来 Google Workspace ユーザーを追加した場合の互換性

### Q4: `USER_DEPLOYING` を維持したまま gmail.com ユーザーで運用する設計は問題ないか？
- `USER_DEPLOYING` = スクリプトオーナーの権限で実行
- gmail.com ユーザーには `USER_ACCESSING` が使えない（OAuth同意画面の制約）
- GIS でクライアント側認証 + サーバー側は userKey でユーザー識別
- **セキュリティ**: userKey の偽装リスク（localStorage を手動で書き換え可能）

### Q5: `renderButton()` を使う場合の注意点
- GAS Web アプリは iframe 内で動作する
- `renderButton()` は iframe 内でも動作するか？
- Google の Same-Origin Policy / CSP の制約はないか？

---

## 10. 参考: 現在のコード行番号マップ

### 土木 (doboku-14w-training)

| 関数 | ファイル | 行 |
|------|---------|-----|
| `getClientUserKey()` | src/index.html | 1080 |
| `setClientUserKey()` | src/index.html | 1083 |
| `showRegistrationScreen_()` | src/index.html | 1087 |
| `initGoogleSignIn_()` | src/index.html | 1119 |
| `showGoogleButton_()` | src/index.html | 1139 |
| `triggerGoogleSignIn_()` | src/index.html | 1153 |
| `handleGoogleCredential_()` | src/index.html | 1180 |
| `showLoginScreen_()` | src/index.html | 1211 |
| `isLoginError_()` | src/index.html | 1216 |
| `handleApiError_()` | src/index.html | 1225 |
| `loadHome()` | src/index.html | 1259 |
| `renderHome()` | src/index.html | 1303 |
| `DOMContentLoaded → loadHome` | src/index.html | 4141 |
| `getActiveEmail_()` | src/logic.gs | 76 |
| `getUserContext_()` | src/logic.gs | 102 |
| `ensureUser_()` | src/logic.gs | 124 |
| `apiGetHome()` | src/api.gs | 20 |
| `apiLoginWithGoogle()` | src/auth.gs | 11 |
| `apiGetGoogleClientId()` | src/auth.gs | 76 |

### 建築 (archi-16w-training)

| 関数 | ファイル | 行 |
|------|---------|-----|
| `getClientUserKey()` | src/index.html | 958 |
| `setClientUserKey()` | src/index.html | 961 |
| `showRegistrationScreen_()` | src/index.html | 965 |
| `initGoogleSignIn_()` | src/index.html | 993 |
| `showGoogleButton_()` | src/index.html | 1009 |
| `triggerGoogleSignIn_()` | src/index.html | 1020 |
| `handleGoogleCredential_()` | src/index.html | 1041 |
| `showLoginScreen_()` | src/index.html | 1071 |
| `isLoginError_()` | src/index.html | 1076 |
| `handleApiError_()` | src/index.html | 1086 |
| `loadHome()` | src/index.html | 1119 |
| `renderHome()` | src/index.html | 1163 |
| `DOMContentLoaded → loadHome` | src/index.html | 3594 |
| `getActiveEmail_()` | src/logic.gs | 76 |
| `getUserContext_()` | src/logic.gs | 102 |
| `ensureUser_()` | src/logic.gs | 124 |
| `apiGetHome()` | src/api.gs | 20 |
| `apiLoginWithGoogle()` | src/auth.gs | 11 |
| `apiGetGoogleClientId()` | src/auth.gs | 76 |
