# QA Practice App - Basic Operations Test Plan

## Executive Summary
- Target: `http://127.0.0.1:5000/` QA Practice App, a role-based product inventory manager with admin/user personas.
- Scope: Core authentication, product listing/search, CRUD operations, role permissions, known intentional defects (500 error, XSS, deletion confirmation gap), UI state cues.
- Out of Scope: API endpoints, performance testing, persistence across browser reloads beyond basic expectations.
- Assumptions: Database in seeded state; browser cache cleared; tester starts from login page; no parallel modifications by other users; admin credentials `admin/admin_password`, user credentials `user/user_password`.

## Scenario 1: Admin Login Success
- **Assumptions:** Start on login page, no active session.
- **Steps:**
  1. Enter `admin` in `ユーザーID`.
  2. Enter `admin_password` in `パスワード`.
  3. Click `ログイン`.
- **Expected Results:** Redirects to `products` list; toast "ログインしました"; header shows "ログイン中: admin (admin)"; logout button visible.
- **Success Criteria:** All expectations met without error dialogs.
- **Failure Conditions:** Invalid credential message, unexpected navigation, or HTTP error.

## Scenario 2: Login Fails With Invalid Password
- **Assumptions:** Start on login page; credentials untouched.
- **Steps:**
  1. Enter `admin` in `ユーザーID`.
  2. Enter incorrect password (e.g., `wrong_pass`).
  3. Click `ログイン`.
- **Expected Results:** Login remains on same page; inline error or flash message indicates authentication failure; fields stay editable; no navigation to products.
- **Success Criteria:** App blocks access without session creation.
- **Failure Conditions:** Access granted with wrong credentials; unhandled exception; ambiguous feedback.

## Scenario 3: Admin Filters Products By Category And Price
- **Assumptions:** Logged in as admin on products list with seeded data.
- **Steps:**
  1. Select `書籍` in `カテゴリ` dropdown.
  2. Set `価格帯` min to `2000` and max to `4000`.
  3. Leave keyword blank and click `検索`.
- **Expected Results:** Table reloads showing only book entries with prices within range (IDs 1 and 2 by default); rows outside criteria hidden; filters persist in form inputs.
- **Success Criteria:** Results match filter logic, no unintended products displayed.
- **Failure Conditions:** Items outside range appear; 0 results despite matches; filters reset unexpectedly.

## Scenario 4: Keyword "バグ票" Triggers Intentional 500 Error
- **Assumptions:** Logged in as admin; aware of intentional defect.
- **Steps:**
  1. Enter `バグ票` in `キーワード`.
  2. Leave other filters blank and click `検索`.
- **Expected Results:** Server responds with 500 error page (Werkzeug debugger runtime error message).
- **Success Criteria:** Defect reproduces consistently for training documentation.
- **Failure Conditions:** Search succeeds or different error state occurs.

## Scenario 5: Admin Registers New Product With Valid Data
- **Assumptions:** Logged in as admin; products list visible.
- **Steps:**
  1. Click `新規商品を登録`.
  2. Enter `テストノート` as 商品名.
  3. Choose `その他` for カテゴリ.
  4. Set 価格 to `1200`.
  5. Set 在庫数 to `8`.
  6. Enter `UI検証用のサンプル商品。` as 商品説明.
  7. Ensure ステータス remains `準備中`.
  8. Click `登録`.
- **Expected Results:** Redirect to list; success flash message; new row appended with entered values; 在庫数8 displays "残りわずか".
- **Success Criteria:** Data persists correctly; list ordering and formatting intact.
- **Failure Conditions:** Validation fires erroneously; redirect missing; incorrect formatting (price, status, stock badge).

## Scenario 6: Product Registration Validation Boundaries
- **Assumptions:** Logged in as admin, on registration form.
- **Steps:**
  1. Attempt submission with all required fields blank.
  2. Enter 商品名 of 51 characters and submit.
  3. Enter 価格 `-1`, then `1000001`, submitting each time.
  4. Enter 在庫数 `-1`, then `1000`, submitting each time.
  5. Enter non-numeric characters in 価格 and 在庫数 and submit.
- **Expected Results:** App blocks submission, highlighting offending fields with clear validation messages per rule; no product created; previously valid field values retained.
- **Success Criteria:** Each boundary condition produces appropriate validation feedback without server crash.
- **Failure Conditions:** Invalid data accepted; generic/unclear message; fields reset unexpectedly.

## Scenario 7: Admin Updates Product And Maintains Valid Status Transition
- **Assumptions:** Logged in as admin; product with status `準備中` exists (seed ID 3).
- **Steps:**
  1. Open `編集` for product ID 3.
  2. Change ステータス to `公開中`.
  3. Adjust 在庫数 to `15`.
  4. Click `更新`.
- **Expected Results:** Redirect to list with success message; row reflects status `公開中`, 在庫あり badge; changes persist after refresh.
- **Success Criteria:** Allowed state transition succeeds and derived UI updates accordingly.
- **Failure Conditions:** Transition blocked incorrectly; derived badges not updated; data loss.

## Scenario 8: Admin Prevented From Invalid Status Transition
- **Assumptions:** Logged in as admin; product with status `公開中` exists (seed ID 1).
- **Steps:**
  1. Open `編集` for product ID 1.
  2. Attempt to select `準備中` (forbidden transition).
  3. Click `更新`.
- **Expected Results:** Submission blocked with clear error (client-side disable or server validation); status remains `公開中`.
- **Success Criteria:** Business rule enforcement prevents illegal transition with feedback.
- **Failure Conditions:** Transition succeeds, or app crashes/silently reverts without notice.

## Scenario 9: Admin Deletes Product Without Confirmation Prompt
- **Assumptions:** Logged in as admin with deletable product available.
- **Steps:**
  1. Note total row count.
  2. Click `削除` for a non-critical product (e.g., ID 5).
- **Expected Results:** Immediate deletion occurs without confirmation dialog (intentional UX gap); row removed; success message displayed; row count decrements by one.
- **Success Criteria:** Deletion executes instantly, highlighting need for confirmation improvement.
- **Failure Conditions:** Confirmation unexpectedly appears; deletion fails; incorrect row removed.

## Scenario 10: User Role Sees Restricted UI
- **Assumptions:** Logged out; will log in as `user`.
- **Steps:**
  1. Log in with `user/user_password`.
  2. Observe products list toolbar and row actions.
- **Expected Results:** No `新規商品を登録` link; `削除` buttons absent; `編集` links still visible; header shows user identity.
- **Success Criteria:** UI elements align with role permissions.
- **Failure Conditions:** User sees admin-only controls; unauthorized options clickable.

## Scenario 11: User Edits Product Within Allowed Scope
- **Assumptions:** Logged in as user; product ID 3 accessible.
- **Steps:**
  1. Open `編集` for product ID 3.
  2. Update 在庫数 to `7` and change ステータス to `公開中` (allowed path from 準備中).
  3. Click `更新`.
- **Expected Results:** Update succeeds; list reflects new values; no admin-only fields exposed.
- **Success Criteria:** User can edit and persist permitted fields; derived badges update.
- **Failure Conditions:** Save blocked without justification; unauthorized fields exposed; error message referencing permissions.

## Scenario 12: XSS Payload In Product Description (Intentional Defect)
- **Assumptions:** Logged in as admin; target product available for editing or creation.
- **Steps:**
  1. Edit existing product (e.g., ID 1) or create new product.
  2. Enter `<script>alert('XSS')</script>` in 商品説明.
  3. Save changes.
  4. Return to products list and view rendered description.
- **Expected Results:** Stored XSS executes when row rendered (intentional defect); alert dialog appears.
- **Success Criteria:** Defect reproduced for training; risk documented.
- **Failure Conditions:** Payload sanitized (would indicate deviation from practice spec) or page crash.

## Scenario 13: 在庫数に応じたステータス表示
- **Assumptions:** Logged in as admin; ability to adjust stock values.
- **Steps:**
  1. Edit product to set 在庫数 `0`, save, and observe row.
  2. Edit same product to set 在庫数 `5`, save, and observe row.
  3. Edit same product to set 在庫数 `15`, save, and observe row.
- **Expected Results:**
  - Stock `0`: Row shows "在庫切れ" with red background.
  - Stock `1-10`: Row shows "残りわずか" with yellow background.
  - Stock `>10`: Row shows "在庫あり" without highlight.
- **Success Criteria:** Visual cues match thresholds; background styles persist across refresh.
- **Failure Conditions:** Incorrect labels/colors; inconsistent CSS application; caching issues.

## Scenario 14: Logout Terminates Session
- **Assumptions:** Logged in as any role; products page open.
- **Steps:**
  1. Click `ログアウト`.
  2. Attempt to access `/products` via browser address bar or back navigation.
- **Expected Results:** Redirect to login page with flash message; `/products` requires re-authentication.
- **Success Criteria:** Session invalidated, preventing unauthorized access.
- **Failure Conditions:** `/products` accessible post-logout; stale session persists without credentials prompt.
