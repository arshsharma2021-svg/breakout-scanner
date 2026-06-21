# Deploy Your Breakout Scanner — Click-by-Click Guide

This gets you a real, live website link that re-scans automatically every
hour during market hours, for free, with no server to maintain.

**Total time: ~15 minutes, one-time setup.**

---

## Before you start

Make sure you've created your GitHub account at https://github.com/signup
(you said you were doing this already — if not, do it now).

---

## STEP 1 — Create the repository

1. Go to https://github.com/new
2. **Repository name:** type `breakout-scanner`
3. **Public or Private:** choose **Public** (required for free GitHub Pages + unlimited free Actions minutes; your code/strategy logic will be visible to anyone, but your `results.json` data isn't sensitive — it's just public stock prices)
4. Leave everything else as default — do NOT check "Add a README"
5. Click the green **Create repository** button
6. You'll land on a page with setup instructions — ignore them, we'll upload differently

---

## STEP 2 — Upload the files

1. On your new (empty) repo page, click **"uploading an existing file"** (it's a blue link in the instructions box)
2. Drag in these files/folders, keeping their structure:
   - `scanner.py`
   - `requirements.txt`
   - `index.html`
   - the whole `data` folder (containing `results.json`)
   - the whole `.github` folder (containing `workflows/scan.yml`)

   **Important:** GitHub's drag-and-drop upload preserves folder structure if you drag the actual folders.
   If your browser only lets you drag files (not folders), see the "Alternative: GitHub Desktop" section
   at the bottom — it's actually easier for the `.github` folder.

3. Scroll down, type a commit message like "Initial upload"
4. Click **Commit changes**

---

## STEP 3 — Turn on GitHub Pages (this creates your live link)

1. In your repo, click **Settings** (top right tab)
2. In the left sidebar, click **Pages**
3. Under "Build and deployment" → **Source**, select **Deploy from a branch**
4. Under **Branch**, select **main** and folder **/ (root)**
5. Click **Save**
6. Wait ~1-2 minutes, then refresh the page — you'll see a green box:
   **"Your site is live at https://YOURUSERNAME.github.io/breakout-scanner/"**

**That URL is your permanent link.** Bookmark it. It will always show your latest scan.

---

## STEP 4 — Turn on and test the scanner (GitHub Actions)

1. Click the **Actions** tab at the top of your repo
2. You may see a banner asking to enable workflows — click **"I understand my workflows, go ahead and enable them"**
3. In the left sidebar, click **Run Breakout Scanner**
4. Click the **Run workflow** dropdown (right side) → **Run workflow** button
5. Wait ~2-3 minutes, then refresh — you'll see a run with a yellow dot (running) then green check (done)
6. Click into that run to watch the live log — you'll see it scanning each ticker
7. Once it finishes (green check), go back to your live site link from Step 3 and refresh — you should now see real results

**From here on, it runs automatically** every hour, 9:30am-4:30pm ET, Monday-Friday — no further action needed.

---

## How to check on it later

- **See latest results:** visit your `github.io` link anytime
- **See scan history / logs:** Actions tab → Run Breakout Scanner → click any run
- **Force an immediate re-scan:** Actions tab → Run Breakout Scanner → Run workflow
- **Change strategy parameters:** edit the `CONFIG` dict at the top of `scanner.py` directly in the GitHub web editor (click the file → pencil icon to edit → commit)

---

## If a scheduled run fails

GitHub emails the account owner automatically when a scheduled Action fails.
Click into the failed run's log — the per-ticker error handling means a single
bad ticker won't fail the whole run, so a full failure usually means either:
- yfinance changed something (check the error message, may need a `requirements.txt` version bump)
- GitHub had a temporary outage (rare, just re-run it manually)

---

## Alternative: GitHub Desktop (easier for folders)

If the drag-and-drop upload in Step 2 is fighting you over the `.github` folder
(some browsers don't upload hidden-style folders well via drag-and-drop):

1. Download GitHub Desktop: https://desktop.github.com
2. Install it, sign in with your GitHub account
3. File → Clone Repository → select your `breakout-scanner` repo → Clone
4. It opens a local folder on your computer — copy ALL the scanner files into that folder using File Explorer/Finder (this preserves the `.github` folder correctly)
5. Go back to GitHub Desktop — it will show all the new files as changes
6. Type a commit message at the bottom left, click **Commit to main**
7. Click **Push origin** at the top
8. Continue with Step 3 above

---

## Cost confirmation

- GitHub Pages: free, unlimited, for public repos
- GitHub Actions: free tier is 2,000 minutes/month for public repos — this scan
  takes roughly 1-3 minutes per run × ~35 runs/week (hourly, market hours) ≈
  150-450 minutes/month. Comfortably within the free tier with room to spare.
- yfinance: free, no key
- **Total: $0/month**
