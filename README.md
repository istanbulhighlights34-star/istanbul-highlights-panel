# Istanbul Highlights automatic Instagram posts

Account: **@istanbul.highlights**. The bot publishes up to three English photo posts per day from the English place pages at **istanbulhighlights.com**. No photo/video uploads, outside image searches, or paid AI services.

## Content and design

Only same-origin `/images/` photographs actually listed on the selected English article are allowed. The place name and a short introductory paragraph come from that article. Each caption ends with **Discover more at istanbulhighlights.com**, the original place URL, and English hashtags. The 1080×1350 frame matches the site's navy `#0B0F19`, gold `#C5A059`, serif identity and circular IH logo. Places and photographs rotate by least recent use.

## Schedule

Daily **09:00, 11:00, 17:00 Europe/Istanbul** (UTC 06:00, 08:00, 14:00). GitHub Actions checks at the target minute and 15, 30, 45 minutes later for delayed runs. A date/time slot can produce at most one upload attempt. Delays up to 90 minutes are accepted; missed older slots are not sent in a burst. Free GitHub schedules may be delayed or dropped, so exact times and three successful posts cannot be guaranteed. Public standard runners are used; no paid runner or Render cron is required.

## Connection

In this repository's **Settings → Secrets and variables → Actions**, add `IG_PASSWORD` and `IG_SESSION` for **istanbul.highlights**. Never place these values in code, issues or publication-state.json. IG_SESSION is the JSON session exported by instagrapi for this account. The bot verifies the logged-in account username before uploading. This uses instagrapi, the same session approach as the earlier project, rather than Meta's official API. Login challenges may need account-owner action.

Do not run Actions until the account secrets are ready. No successful connection or Instagram publication has been verified yet.

## Persistence and status

`publication-state.json` stores only public source URLs, English captions, times and publication status. GitHub's built-in workflow token writes these records atomically. A reservation is committed before Instagram is contacted; uploading is committed before the upload call. A timeout leaves `uncertain` or `uploading`; scheduled retries do not repeat it. If a state commit fails after successful upload, the earlier uploading reservation prevents duplicates. Check the Instagram account manually before any recovery. Once all destinations have been used, the bot rotates back to the least recently used places/photos.

## Render panel

Deploy the Free Python web service using render.yaml. It is a password-protected, read-only monitor. Set `PANEL_PASSWORD` and a separate random `PANEL_SESSION_SECRET`. No Instagram password, Supabase account, paid database or storage is needed on Render. The panel reads publication metadata from the public repository. Free Render may sleep; this does not stop GitHub publication jobs. Status commits to main also trigger Render auto-deploy unless its automatic deploy is disabled after the initial deployment.

## Local preview and checks

Install `requirements.txt` in a venv, then run `python run_local.py`. The temporary private panel password is printed locally. `python automatic.py --preview` creates a site-photo example in the ignored `preview/` folder without publishing. Run `python -m unittest discover -s tests -v` for schedule, source restrictions, duplicate prevention, uncertain upload and upload-route removal checks.

## Cost limits

Render Free and public GitHub standard runners are used. Render free hours and bandwidth/build quotas still apply: https://render.com/docs/free. GitHub schedules can be delayed and public repository schedules can disable after inactivity: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule. No upgrade or paid service is enabled by this project.
