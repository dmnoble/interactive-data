
# ✅ Phase 10: Debugging Completion Checklist

This checklist ensures that all GUI functionality, view selection, sorting, and filtering work correctly in the Interactive Data Workspace.

---

## ✅ Saved View + GUI Behavior

| Category       | ✅ Behavior                                      | Manual Test                                                |
|----------------|--------------------------------------------------|-------------------------------------------------------------|
| **Startup**    | Default saved view applies sort                 | App starts → verify visible order and arrow                |
|                | Sort Result column shows populated values       | Confirm column values match expectation                    |
|                | Ascending/Descending selector reflects setting  | Launch → dropdown matches saved view                       |

---

## ✅ Switching Views

| Category       | ✅ Behavior                                      | Manual Test                                                |
|----------------|--------------------------------------------------|-------------------------------------------------------------|
| **Views**      | No Sort Key resets to sort by `id`              | Switch to simple search/structured-only view               |
|                | Sort Key view auto-sorts table                  | Switch to Sort Key view → no Apply click needed            |
|                | Sort Result column updates                      | Switch to Sort Key view → column refreshes                 |
|                | Sort arrow updates correctly                    | Confirm header arrow on correct column & direction         |
|                | Asc/Desc selector syncs with view               | Check dropdown reflects newly selected view                |

---

## ✅ Clearing Controls

| Category         | ✅ Behavior                                   | Manual Test                                                |
|------------------|-----------------------------------------------|-------------------------------------------------------------|
| **Clear Buttons**| Sort Clear removes Sort Result values         | Hit Sort Clear → column becomes blank                      |
|                  | Filter Clear resets structured/custom fields  | Hit Filter Clear → inputs reset                            |
|                  | Table returns to id-sorted                    | Clear sort/filter → verify row order = ids                |

---

## ✅ Advanced UX

| Category         | ✅ Behavior                                   | Manual Test                                                |
|------------------|-----------------------------------------------|-------------------------------------------------------------|
| **Filters & Help**| Highlighting works for basic search terms     | Search “Alice” → text gets yellow highlight                |
|                  | Structured filter ops function correctly      | e.g., age > 30 → correct subset shown                      |
|                  | Combined filters work                         | Structured + custom = correct intersection                 |
|                  | Sort Help includes split(), `in`, etc.        | Click Help → see extended example list                     |

---

## 🧠 Optional: Stretch Goals

| Goal                                               | Manual Test                                    |
|----------------------------------------------------|------------------------------------------------|
| Re-selecting same saved view resets table state    | Select view again → table refreshes            |
| Sort Result column is always last                  | Scroll right → check position                  |
| Manual header click re-sorts table                 | Click header → sort updates visually           |
